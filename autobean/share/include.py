from typing import Any
import os.path
from beancount.core.data import Directive, Transaction, Open
from beancount import loader
from autobean.utils import error_lib
from autobean.share import utils, directives
from autobean.share.split_postings import split_postings
from autobean.share.link_accounts import link_accounts


def process_ledger(entries: list[Directive], is_nobody: bool, options: dict[str, Any], logger: error_lib.ErrorLogger) -> list[Directive]:
    # For nobody viewpoint, we still fill the residuals but ignore the
    # results so proportionate assertion works.
    filled_entries = split_postings(entries, logger)
    if not is_nobody:
        entries = filled_entries
    else:
        entries = filter_out_share_meta(entries)
    includes = set(options['include'])
    entries = process_included_files(entries, is_nobody, includes, logger)
    entries = filter_out_share_directives(entries)
    # Allow tools to refresh data when included files are updated
    options['include'][:] = list(includes)
    return entries


def process_included_files(entries: list[Directive], is_nobody: bool, includes: set[str], logger: error_lib.ErrorLogger) -> list[Directive]:
    ret = []
    links = []
    entries_by_file = {}
    for entry in entries:
        if include := directives.Include.try_parse(entry):
            if isinstance(include, error_lib.Error):
                logger.log_error(include)
                continue
            entries_by_file[include.filename] = process_include_directive(
                include, is_nobody, includes, logger)
        elif link := directives.Link.try_parse(entry):
            if isinstance(link, error_lib.Error):
                logger.log_error(link)
                continue
            links.append(link)
        else:
            ret.append(entry)
    resolved_entries = link_accounts(entries_by_file, links, logger)
    ret.extend(resolved_entries)
    ret = deduplicate_opens(ret)
    return ret


def process_include_directive(
        include: directives.Include,
        is_nobody: bool,
        includes: set[str],
        logger: error_lib.ErrorLogger) -> list[Directive]:
    path = os.path.join(os.path.dirname(include.custom.meta['filename']), include.filename)
    entries, errors, options = loader.load_file(path)
    logger.log_loading_errors(errors, include.custom)
    entries = process_ledger(entries, is_nobody, options, logger)
    includes.update(set(options['include']))
    return entries


def filter_out_share_directives(entries: list[Directive]) -> list[Directive]:
    return [
        entry
        for entry in entries
        if not directives.is_autobean_share_directive(entry)
    ]

def filter_out_share_meta(entries: list[Directive]) -> list[Directive]:
    ret = []
    for entry in entries:
        entry = utils.strip_meta(entry)
        if isinstance(entry, Transaction):
            entry.postings[:] = [
                utils.strip_meta(posting)
                for posting in entry.postings
            ]
        ret.append(entry)
    return ret
    

def deduplicate_opens(entries: list[Directive]) -> list[Directive]:
    ret = []
    open_accounts = set()
    for entry in entries:
        if not isinstance(entry, Open):
            ret.append(entry)
        elif entry.account not in open_accounts:
            open_accounts.add(entry.account)
            ret.append(entry)
    return ret

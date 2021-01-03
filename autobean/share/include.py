from typing import List, Dict, Tuple, Set, Any
from collections import namedtuple
import os.path
from beancount.core.data import Directive, Transaction, Custom, Open, new_metadata
from beancount import loader
from autobean.utils.error_logger import ErrorLogger
from autobean.share import utils
from autobean.share.include_context import include_context
from autobean.share.fill_residuals import fill_residuals
from autobean.share.select_viewpoint import select_viewpoint
from autobean.share.map_residual_accounts import map_residual_accounts
from autobean.share.open_subaccounts import open_subaccounts


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')


def process_ledger(entries: List[Directive], is_nobody: bool, options: Dict[str, Any], logger: ErrorLogger) -> List[Directive]:
    # For nobody viewpoint, we still fill the residuals but ignore the
    # results so proportionate assertion works.
    filled_entries = fill_residuals(entries, options, logger)
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


def process_included_files(entries: List[Directive], is_nobody: bool, includes: Set[str], logger: ErrorLogger) -> List[Directive]:
    ret = []
    for entry in entries:
        if isinstance(entry, Custom) and entry.type == 'autobean.share.include':
            file_entries = process_include_directive(entry, is_nobody, includes, logger)
            ret.extend(file_entries)
        else:
            ret.append(entry)
    ret = deduplicate_opens(ret)
    return ret


def process_include_directive(entry: Custom, is_nobody: bool, includes: Set[str], logger: ErrorLogger) -> List[Directive]:
    if len(entry.values) != 1:
        logger.log_error(InvalidDirectiveError(
            entry.meta, 'autobean.share.include expects 1 argument but {} are given'.format(len(entry.values)), entry
        ))
        return []
    if entry.values[0].dtype is not str:
        logger.log_error(InvalidDirectiveError(
            entry.meta, 'autobean.share.include expects a path as argument', entry
        ))
        return []
    path = entry.values[0].value
    path = os.path.join(os.path.dirname(entry.meta['filename']), path)
    entries, errors, options = loader.load_file(path)
    logger.log_loading_errors(errors, entry)
    entries = process_ledger(entries, is_nobody, options, logger)
    includes.update(set(options['include']))
    return entries


def filter_out_share_directives(entries: List[Directive]) -> List[Directive]:
    return [
        entry
        for entry in entries
        if not utils.is_autobean_share_directive(entry)
    ]

def filter_out_share_meta(entries: List[Directive]) -> List[Directive]:
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
    

def deduplicate_opens(entries: List[Directive]) -> List[Directive]:
    ret = []
    open_accounts = set()
    for entry in entries:
        if not isinstance(entry, Open):
            ret.append(entry)
        elif entry.account not in open_accounts:
            open_accounts.add(entry.account)
            ret.append(entry)
    return ret

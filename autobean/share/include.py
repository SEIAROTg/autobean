from typing import Any, Iterable, Optional
import os.path
from beancount.core.data import Custom, Directive, Open, Close, entry_sortkey
from beancount import loader
from autobean.utils import error_lib, plugin_lib
from . import link_accounts


@plugin_lib.plugin('autobean.share.include')
class IncludePlugin(plugin_lib.BasePlugin):

    def process(self, entries: list[Directive], options: dict[str, Any], arg: Optional[str]) -> Iterable[Directive]:
        self._enabled = True
        self._includes = set(options['include'])
        self._entries_by_file = dict[str, list[Directive]]()
        self._links = list[link_accounts.Link]()
        entries = list(super().process(entries, options, arg))
        entries += link_accounts.link_accounts(
            self._entries_by_file, self._links, self._error_logger)
        entries = deduplicate_open_close(entries)
        options['include'] = list(self._includes)
        return entries

    def _check_enabled(self, entry: Custom) -> None:
        if not self._enabled:
            raise error_lib.PluginException(
                f'Cannot use {entry.type} while autobean.share is disabled')

    @plugin_lib.handle_custom('autobean.share.enable', 'exactly one bool')
    def handle_enable(self, entry: Custom, enable: bool) -> Iterable[Directive]:
        self._enabled = enable
        yield entry

    @plugin_lib.handle_custom('autobean.share.include', 'exactly one path')
    def handle_include(self, entry: Custom, path: str) -> Iterable[Directive]:
        self._check_enabled(entry)
        path = os.path.join(os.path.dirname(entry.meta['filename']), path)
        if path in self._entries_by_file:
            return ()
        entries, errors, options = loader.load_file(path)
        self._error_logger.log_errors(errors)
        self._includes.update(options['include'])
        self._entries_by_file[path] = entries
        return ()

    @plugin_lib.handle_custom('autobean.share.link', 'path to an included ledger, an account in it, path to another included ledger, and an account in it')
    def handle_link(self, entry: Custom, path: str, account: plugin_lib.Account, complement_path: str, complement_account: plugin_lib.Account) -> Iterable[Directive]:
        self._check_enabled(entry)
        path = os.path.join(os.path.dirname(entry.meta['filename']), path)
        complement_path = os.path.join(os.path.dirname(entry.meta['filename']), complement_path)
        self._links.append(link_accounts.Link(
            path=path,
            account=account,
            complement_path=complement_path,
            complement_account=complement_account,
            custom=entry,
        ))
        return ()


def deduplicate_open_close(entries: list[Directive]) -> list[Directive]:
    """Deduplicates Open / Close directives.
    
    This deduplicates Open / Close directives in a simple way because duplication inside each file should have been
    caught during loading.
    """
    results = []
    opened_accounts = set()
    closed_accounts = set()
    for entry in sorted(entries, key=entry_sortkey):
        if isinstance(entry, Open):
            if entry.account not in opened_accounts:
                opened_accounts.add(entry.account)
                results.append(entry)
        elif isinstance(entry, Close):
            if entry.account not in closed_accounts:
                closed_accounts.add(entry.account)
                results.append(entry)
        else:
            results.append(entry)
    return results

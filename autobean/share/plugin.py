from typing import List, Dict, Tuple
from beancount.core.data import Directive
from beancount.ops import validation
from autobean.utils.error_logger import ErrorLogger
from autobean.share.include_context import include_context
from autobean.share.include import process_ledger
from autobean.share.fill_residuals import fill_residuals
from autobean.share.map_residual_accounts import map_residual_accounts
from autobean.share.open_subaccounts import open_subaccounts
from autobean.share.select_viewpoint import select_viewpoint


def plugin(entries: List[Directive], options: Dict, viewpoint: str) -> Tuple[List[Directive], List]:
    is_top_level = include_context['is_top_level']
    if not is_top_level:
        return entries, []
    include_context['is_top_level'] = False
    logger = ErrorLogger()
    errors = validation.validate(entries, options)
    logger.log_errors(errors)
    entries = process_ledger(entries, viewpoint == 'nobody', options, logger)
    if viewpoint != 'nobody':
        entries = fill_residuals(entries, options)
        entries = select_viewpoint(entries, viewpoint, logger)
        entries = map_residual_accounts(entries, logger)
        entries = open_subaccounts(entries, logger)
    include_context['is_top_level'] = True
    return entries, logger.errors

from ..base import RawTokenModel


class Placeholder(RawTokenModel):
    RULE = 'PLACEHOLDER'

    @classmethod
    def from_default(cls) -> 'Placeholder':
        return cls('')

    def _clone(self) -> 'Placeholder':
        return Placeholder('')

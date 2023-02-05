from typing import Callable, Dict, Iterable


class Chat:
    def __init__(self,
                 active: bool,
                 members: Dict[int, str],
                 get_name: Callable[[int], str]):
        self._active = active
        self._members = members
        self._get_name = get_name

    @property
    def is_active(self) -> bool:
        return self._active

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False

    def add_member(self, user_id: int):
        self._members[user_id] = self._get_name(user_id)

    @property
    def members(self):
        return self._members

    def __getitem__(self, user_id: int) -> str:
        return self._members[user_id]

    def __contains__(self, user_id: int) -> bool:
        return user_id in self._members

    def __iter__(self) -> Iterable[int]:
        return iter(self._members)

    def __len__(self) -> int:
        return len(self._members)

    @classmethod
    def from_dict(cls,
                  data: dict,
                  get_name: Callable[[int], str]):
        return cls(data.get('active', False),
                   data.get('members', ()),
                   get_name)

    def to_dict(self):
        return {
            'active': self.is_active,
            'members': self._members
        }

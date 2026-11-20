class Department:
    """Department entity holding department profile information (Section 16 & 45.4.7)."""
    def __init__(
        self,
        departmentId: str,
        name: str,
        headOfDept: str = "",
        contactInfo: str = ""
    ):
        self._departmentId = departmentId
        self._name = name
        self._headOfDept = headOfDept
        self._contactInfo = contactInfo

    @property
    def departmentId(self) -> str:
        return self._departmentId

    @departmentId.setter
    def departmentId(self, value: str):
        self._departmentId = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def headOfDept(self) -> str:
        return self._headOfDept

    @headOfDept.setter
    def headOfDept(self, value: str):
        self._headOfDept = value

    @property
    def contactInfo(self) -> str:
        return self._contactInfo

    @contactInfo.setter
    def contactInfo(self, value: str):
        self._contactInfo = value

    def to_dict(self):
        return {
            "departmentId": self._departmentId,
            "name": self._name,
            "headOfDept": self._headOfDept,
            "contactInfo": self._contactInfo
        }

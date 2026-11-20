class DomainArea:
    """Quality Criterion / Domain Area (Section 45.4.8)."""
    def __init__(self, domainId: str, name: str, description: str = ""):
        self.domainId = domainId
        self.name = name
        self.description = description

    def to_dict(self):
        return {
            "domainId": self.domainId,
            "name": self.name,
            "description": self.description
        }

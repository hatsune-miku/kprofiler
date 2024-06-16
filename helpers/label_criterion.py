class LabelCriterion:
    def __init__(self, keyword: str, label: str):
        self.keyword = keyword
        self.label = label
    
    def match(self, text: str) -> bool:
        return self.keyword in text

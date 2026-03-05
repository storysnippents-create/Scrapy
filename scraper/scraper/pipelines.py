class CleanTextPipeline:
    """Strip whitespace from string fields and deduplicate lists."""

    def process_item(self, item, spider):
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = value.strip()
            elif isinstance(value, list):
                item[key] = list(dict.fromkeys(v.strip() if isinstance(v, str) else v for v in value))
        return item

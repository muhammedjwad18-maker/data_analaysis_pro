class AppConfig:
    def __init__(self):
        self.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        self.SUPPORTED_FORMATS = ['csv', 'xlsx', 'json', 'parquet']
        self.CHART_THEMES = ['plotly', 'plotly_white', 'plotly_dark']
        self.DEFAULT_SETTINGS = {
            'theme': 'plotly',
            'language': 'en',
            'auto_save': True,
            'notifications': True
        }
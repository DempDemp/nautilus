class Settings(object):
    def setup(self, mod):
        for setting in dir(mod):
            if setting.isupper():
                setattr(self, setting, getattr(mod, setting))

settings = Settings()

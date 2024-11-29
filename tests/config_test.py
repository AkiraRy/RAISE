
from config import SettingsManager

if __name__ == '__main__':
    settings_manager = SettingsManager().load_settings()
    # settings_manager.config.pubsub.input_message_topic = 'new_topic'
    print(settings_manager.config.brain)
    print(settings_manager.config.pubsub)
    settings_manager.save_settings()

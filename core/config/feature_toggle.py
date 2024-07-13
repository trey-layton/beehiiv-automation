import json
import os


class FeatureToggle:
    def __init__(self, config_path):
        self.config_path = config_path
        self.toggles = self.load_toggles()

    def load_toggles(self):
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, "r") as f:
            return json.load(f)

    def save_toggles(self):
        with open(self.config_path, "w") as f:
            json.dump(self.toggles, f, indent=2)

    def is_enabled(self, feature_name):
        return self.toggles.get(feature_name, False)

    def enable_feature(self, feature_name):
        self.toggles[feature_name] = True
        self.save_toggles()

    def disable_feature(self, feature_name):
        self.toggles[feature_name] = False
        self.save_toggles()


# Initialize the FeatureToggle
feature_toggle = FeatureToggle(
    os.path.join(os.path.dirname(__file__), "feature_toggles.json")
)

# At the end of feature_toggle.py
feature_toggle = FeatureToggle(
    os.path.join(os.path.dirname(__file__), "feature_toggles.json")
)

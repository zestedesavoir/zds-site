from django.core.management.base import BaseCommand

from zds.antispam.spam_fields import spam_fields
from zds.antispam.spam_model_manager import SpamModelManager


class Command(BaseCommand):
    def __init__(self):
        # Dynamically extract available models from spam_fields
        available_models = {field["scope"] for field in spam_fields}
        self.help = (
            "Retrain the spam filter model(s) and save them to a file.\n"
            f"The available models are: {', '.join(available_models)}.\n"
            "Use the --model option to specify a model to train, or omit it to train all models."
        )
        super().__init__()

    def add_arguments(self, parser):
        # Dynamically extract available models from spam_fields
        available_models = {field["scope"] for field in spam_fields}
        parser.add_argument(
            "--model",
            type=str,
            choices=available_models,
            help=f"Specify the model to train ({', '.join(available_models)}). If omitted, all models will be trained.",
        )

    def handle(self, *args, **options):
        model_manager = SpamModelManager()

        if options["model"]:
            self.stdout.write(f"Starting retraining of the {options['model']} spam filter model...")
            model_manager.train(options["model"])
            self.stdout.write(f"Retraining of the {options['model']} model completed successfully.")
        else:
            self.stdout.write("Starting retraining of all spam filter models...")
            # Dynamically train all models based on spam_fields
            for model in {field["scope"] for field in spam_fields}:
                model_manager.train(model)
            self.stdout.write("Retraining of all models completed successfully.")

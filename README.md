# Restaurant Assistant Bot

This simple bot uses a knowledge base containing restaurant info to answer user's requests.

The files are consitent with Rasa 2.0.6, but should be backwards-compatible.

## What’s inside this folder?

This folder contains some training data and the main files needed to train and execute the
assistant locally. The `try1` folder consists of the following files:

- **data/nlu.yml** contains training examples for the NLU model
- **data/stories.yml** contains training stories for the Core model
- **actions/actions.py** contains the custom action for querying the knowledge base
- **config.yml** contains the model configuration
- **domain.yml** contains the domain of the assistant
- **endpoints.yml** contains the webhook configuration for the custom action
- **knowledge_base_data.json** contains the data for the knowledge base

## How to use this example?

To train your knowledge base bot, execute
```
rasa train
```
This will store a zipped model file in `models/`.

Start the action server by
```
rasa run actions
```

To chat with the bot on the command line, run
```
rasa shell
```

For more information about the individual commands, please check out the
[documentation](http://rasa.com/docs/rasa/command-line-interface).

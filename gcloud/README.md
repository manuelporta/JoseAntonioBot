create a Google Cloud Function running this command in the same line:
```
gcloud functions deploy joseantonio_bot --runtime python39 --trigger-http --project=python-telegram-v2
```
you can also specify the region by appending the following string to the previous command
```
--region=<region_name>
```
[list of the available regions](https://cloud.google.com/compute/docs/regions-zones)

Some details:

* Here webhook is the name of the function in the `main.py` file
* You need to specify your Telegram token with the `--set-env-vars` option
* `--runtime python38` describe the environment used by our function, Python 3.8 in this case
* `--trigger-http` is the type of trigger associated to this function, you can find here the complete list of triggers
The above command will return something like this:
  
Step three, you need to set up your Webhook URL using this API call:
```
curl "https://api.telegram.org/bot5547486353:AAF9ifGIhLpqYI6HdOFtrKBCsicNLSMqs-I/setWebhook?url=https://us-central1-python-telegram-v2.cloudfunctions.net/joseantonio_bot"
```
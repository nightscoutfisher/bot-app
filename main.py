import sys
import os
import openai

from google.cloud import storage
from google.api_core import page_iterator

from llama_index import Document, SimpleDirectoryReader, GPTListIndex, readers, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
os.environ.get('OPENAI_API_KEY')


@app.route("/")
def user_index():
    return '''
       <H1>Not Found</H1>
    '''

@app.route("/<name>")
def index(name):
    names = list_directories("email-attachment-test","")
    if name in names:
        result = request.args.get("result")
        return render_template("index.html", result=result, data=name)
    else:
        return '''
            <H1>Not Found</H1>
        '''

@app.route("/answer", methods=["POST"])
def answer():
    name = request.form["name"]
    documents = find_index(name)
    index = GPTSimpleVectorIndex.load_from_string(documents)
    question = request.form["question"]
    response = index.query(question, response_mode="compact")
    return redirect(url_for("index", result=response.response, name=name))

def find_index(username):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("email-attachment-test")
    prefix = f"{username}/index_results"

    '''
    # List objects with the given prefix, filtering out folders.
    blob_list = [blob for blob in list(bucket.list_blobs(
        prefix=prefix)) if not blob.name.endswith('/')]

    index_list = []
    index_str = ''
    for blob in blob_list:
        print(blob.name)
        # index_list.append(blob.download_as_string().decode())
        index_str += blob.download_as_string().decode()
    # documents = [Document(t) for t in index_list]
    print(type(index_str))

    return index_str
    '''

    blob = bucket.get_blob(f"{prefix}/index.json")
    index_str = blob.download_as_string().decode()
    return index_str


def _item_to_value(iterator, item):
    return item[:-1]

def list_directories(bucket_name, prefix):
    if prefix and not prefix.endswith('/'):
        prefix += '/'

    extra_params = {
        "projection": "noAcl",
        "prefix": prefix,
        "delimiter": '/'
    }

    gcs = storage.Client()

    path = "/b/" + bucket_name + "/o"

    iterator = page_iterator.HTTPIterator(
        client=gcs,
        api_request=gcs._connection.api_request,
        path=path,
        items_key='prefixes',
        item_to_value=_item_to_value,
        extra_params=extra_params,
    )

    return [x for x in iterator]

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

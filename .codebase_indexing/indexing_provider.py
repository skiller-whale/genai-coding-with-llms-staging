import os
from pathlib import Path
from flask import Flask, jsonify, request
from langchain_core.vectorstores import InMemoryVectorStore
from langchain.embeddings import CacheBackedEmbeddings
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.storage import LocalFileStore


CODEBASE = '/codebase'


def get_attendance_id(path='/app/sync/attendance_id'):
    """
    Get the attendance ID from a file.
    Args:
        path (str): The path to the file containing the attendance ID.
    Returns:
        str: The attendance ID."""
    with open(path, 'r') as f:
        return f.read().strip()


class CodebaseIndexer:
    """A helper class to index a codebase and provide search functionality."""
    INDEX_CACHE_PATH = './.index_cache'
    VECTOR_STORE_PATH = './.index_cache/codebase_index.p'
    EMBEDDINGS_MODEL = 'amazon.titan-embed-text-v2:0'
    SW_ENDPOINT = 'https://bedrock-runtime.aws-proxy.skillerwhale.com/'
    REGION = 'eu-west-1'
    DIMENSIONS = 256

    def __init__(self, attendance_id, path):
        self.attendance_id = attendance_id
        self.path = path
        self.embeddings = BedrockEmbeddings(
            model_id=self.EMBEDDINGS_MODEL,
            endpoint_url=self.SW_ENDPOINT,
            region_name=self.REGION,
            aws_access_key_id=self.attendance_id,
            aws_secret_access_key='<unused>',
            model_kwargs={ 'dimensions': self.DIMENSIONS }
        )

        self.store = LocalFileStore(self.INDEX_CACHE_PATH)
        self.cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self.embeddings, self.store, key_encoder='sha256'
        )

        self.vector_store = None
        if Path.exists(Path(self.VECTOR_STORE_PATH)):
            print('Loading existing vector store...')
            self.vector_store = InMemoryVectorStore.load(
                self.VECTOR_STORE_PATH,
                self.cached_embeddings
            )

    def index_codebase(self):
        """Index the codebase located at self.path."""
        if self.vector_store:
            print('Vector store already exists, skipping indexing.')
            return

        # skip JSONs failing to parse - in case JSON files are e.g. a top-level array
        # TODO: make more generic
        loader = DirectoryLoader(self.path, silent_errors=True)
        docs = loader.load()

        # Load JSON files as plain text
        json_loader = DirectoryLoader(
            self.path,
            glob="**/*.json",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )

        docs = docs + json_loader.load()
        for d in docs:
            # clip page content
            d.page_content = d.page_content[:1000]

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=0)
        all_splits = text_splitter.split_documents(docs)

        print('Creating new vector store...')
        self.vector_store = InMemoryVectorStore(self.cached_embeddings)
        self.vector_store.add_documents(documents=all_splits)
        self.vector_store.dump(self.VECTOR_STORE_PATH)

    def search_codebase(self, query, k=10):
        """Search the codebase for a query."""
        if not self.vector_store:
            raise ValueError('Vector store not initialized. Please index first.')

        return self.vector_store.similarity_search(query, k)


app = Flask(__name__)
app.config['indexer'] = CodebaseIndexer(get_attendance_id(), path=CODEBASE)
app.config['CODEBASE'] = CODEBASE


@app.route('/search', methods=['GET', 'POST'])
def search():
    """search route to handle indexing and searching."""
    query = request.get_json().get('fullInput')
    results = app.config['indexer'].search_codebase(query, k=10)

    # NOTE: deprecated
    # If the codebase that's indexed doesn't exist, return nothing
    # if request.args.get('codebase') != app.config['CODEBASE']:
    #     return jsonify({'error': 'Invalid codebase'}), 400

    docs = jsonify([
        {
            'description': Path(r.metadata['source']).suffix[1:],
            'content': r.page_content,
            # basename is just the file name
            'name': (_basename := os.path.basename(r.metadata['source'])),
            'uri': {
                # two types of URIs: file and url
                'type': 'file',
                'value': _basename
            }
        }
        for r in results
    ])

    return  docs


if __name__ == '__main__':
    # if you run as a script, generate the index
    app.config['indexer'].index_codebase()
    app.run(host='0.0.0.0', port=5001, debug=False)

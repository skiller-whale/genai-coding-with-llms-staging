from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__)


def load_posts():
    with open('src/data/posts.json') as f:
        return json.load(f)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)

    posts = load_posts()
    start = (page - 1) * 3
    end = start + 3

    return render_template(
        'load_next.html',
        posts=posts[start:end],
        page=page + 1
    )


@app.route('/api/posts', methods=['POST'])
def add_post():
    new_post = request.json
    posts = load_posts()
    posts.append(new_post)
    with open('src/data/posts.json', 'w') as f:
        json.dump(posts, f)
    return jsonify(new_post), 201


if __name__ == '__main__':
    app.run(debug=True)

import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing databse
# But first check to see if we're already running using the Travis-CI config
if os.environ["CONFIG_PATH"] != "posts.config.TravisConfig":
  os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)
        
    def testGetEmptyPosts(self):
      """ Getting posts from an empty database """
      response = self.client.get("/api/posts", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data, [])
      
    def testGetPosts(self):
      """ Getting posts from a populated database """
      postA = models.Post(title="Example Post A", body="Just a test")
      postB = models.Post(title="Example Post B", body="Still a test")
      
      session.add_all([postA, postB])
      session.commit()
      
      response = self.client.get("/api/posts", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(len(data), 2)
      
      postA = data[0]
      self.assertEqual(postA["title"], "Example Post A")
      self.assertEqual(postA["body"], "Just a test")
      
      postB = data[1]
      self.assertEqual(postB["title"], "Example Post B")
      self.assertEqual(postB["body"], "Still a test")
      
    def testGetPost(self):
      """ Getting a single post from a populated database """
      postA = models.Post(title="Example Post A", body="Just a test")
      postB = models.Post(title="Example Post B", body="Still a test")
      
      session.add_all([postA, postB])
      session.commit()
      
      response = self.client.get("/api/posts/{}".format(postB.id), headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      post = json.loads(response.data)
      self.assertEqual(post["title"], "Example Post B")
      self.assertEqual(post["body"], "Still a test")
      
    def testGetNonExistentPost(self):
      """ Getting a single post which doesn't exist """
      response = self.client.get("/api/posts/1", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 404)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Could not find post with id 1")
      
    def testUnsupportedAcceptHeader(self):
      response = self.client.get("/api/posts", headers=[("Accept", "application/xml")])
      
      self.assertEqual(response.status_code, 406)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Request must accept application/json data")
      
    def testDeletePost(self):
      """ Deleting a single post from a populated database """
      postA = models.Post(title="Example Post A", body="Just a test")
      postB = models.Post(title="Example Post B", body="Still a test")
      
      session.add_all([postA, postB])
      session.commit()
      
      response = self.client.delete("/api/posts/{}".format(postB.id), headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 204)
      self.assertEqual(response.mimetype, "application/json")
      self.assertEqual(response.data, '')
      
      response = self.client.get("/api/posts/{}".format(postB.id), headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 404)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Could not find post with id {}".format(postB.id))
      
    def testDeleteNonExistentPost(self):
      """ Deleting a single post which doesn't exist """
      response = self.client.delete("/api/posts/1", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 404)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Could not find post with id 1")
      
    def testGetPostsWithTitle(self):
      """ Filtering posts by title """
      postA = models.Post(title="Post with bells", body="Just a test")
      postB = models.Post(title="Post with whistles", body="Still a test")
      postC = models.Post(title="Post with bells and whistles", body="Another test")
      
      session.add_all([postA, postB, postC])
      session.commit()
      
      response = self.client.get("/api/posts?title_like=whistles", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      posts = json.loads(response.data)
      self.assertEqual(len(posts), 2)
      
      post = posts[0]
      self.assertEqual(post["title"], "Post with whistles")
      self.assertEqual(post["body"], "Still a test")
      
      post = posts[1]
      self.assertEqual(post["title"], "Post with bells and whistles")
      self.assertEqual(post["body"], "Another test")
      
    def testGetPostsWithBody(self):
      """ Filtering posts by body """
      postA = models.Post(title="Example Post A", body="Body with bells")
      postB = models.Post(title="Example Post B", body="Body with whistles")
      postC = models.Post(title="Example Post C", body="Body with bells and whistles")
      
      session.add_all([postA, postB, postC])
      session.commit()
      
      response = self.client.get("/api/posts?body_like=whistles", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      posts = json.loads(response.data)
      self.assertEqual(len(posts), 2)
      
      post = posts[0]
      self.assertEqual(post["title"], "Example Post B")
      self.assertEqual(post["body"], "Body with whistles")
      
      post = posts[1]
      self.assertEqual(post["title"], "Example Post C")
      self.assertEqual(post["body"], "Body with bells and whistles")
      
    def testGetPostsWithTitleAndBody(self):
      """ Filtering posts by both title and body """
      postA = models.Post(title="Title ladies and gentlemen", body="Body with bells")
      postB = models.Post(title="Title gentlemen", body="Body with whistles")
      postC = models.Post(title="Title ladies", body="Body with bells and whistles")
      
      session.add_all([postA, postB, postC])
      session.commit()
      
      response = self.client.get("/api/posts?title_like=gentlemen&body_like=whistles", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      posts = json.loads(response.data)
      self.assertEqual(len(posts), 1)
      
      post = posts[0]
      self.assertEqual(post["title"], "Title gentlemen")
      self.assertEqual(post["body"], "Body with whistles")
      
    def testPostPost(self):
      """ Posting a new post """
      data = {
        "title": "Example Post",
        "body": "Just a test"
      }
      
      response = self.client.post("/api/posts",
                                 data=json.dumps(data),
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 201)
      self.assertEqual(response.mimetype, "application/json")
      self.assertEqual(urlparse(response.headers.get("Location")).path,
                      "/api/posts/1")
      
      data = json.loads(response.data)
      self.assertEqual(data["id"], 1)
      self.assertEqual(data["title"], "Example Post")
      self.assertEqual(data["body"], "Just a test")
      
      posts = session.query(models.Post).all()
      self.assertEqual(len(posts), 1)
      
      post = posts[0]
      self.assertEqual(post.title, "Example Post")
      self.assertEqual(post.body, "Just a test")
      
    def testUnsupportedMimetype(self):
      data = "<xml></xml>"
      response = self.client.post("/api/posts",
                                 data=json.dumps(data),
                                 content_type="application/axml",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 415)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Request must contain application/json data")
      
    def testInvalidData(self):
      """ Posting a post with an invalid body """
      data = {
        "title": "Example Post",
        "body": 32
      }
      
      response = self.client.post("/api/posts",
                                 data=json.dumps(data),
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 422)
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "32 is not of type 'string'")
      
    def testMissingData(self):
      """ Posting a post with a missing body """
      data = {
        "title": "Example Post",
      }
      
      response = self.client.post("/api/posts",
                                 data=json.dumps(data),
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 422)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "'body' is a required property")
      
    def testEditPost(self):
      """ Editing a single post """
      postA = models.Post(title="Example post A", body="Just a test")
      postB = models.Post(title="Example post B", body="Still a test")
      
      session.add_all([postA, postB])
      session.commit()
      
      data = {
        "title": "Edited post B",
        "body": "Now an edited test"
      }
      
      response = self.client.post("/api/posts/{}".format(postB.id),
                                 data=json.dumps(data),
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      self.assertEqual(urlparse(response.headers.get("Location")).path,
                      "/api/posts/2")
      
      data = json.loads(response.data)
      self.assertEqual(data["id"], 2)
      self.assertEqual(data["title"], "Edited post B")
      self.assertEqual(data["body"], "Now an edited test")
      
      post = session.query(models.Post).get(2)
      self.assertEqual(post.title, "Edited post B")
      self.assertEqual(post.body, "Now an edited test")
      
    def testEditPostInvalidData(self):
      """ Editing a post with an invalid body """
      postA = models.Post(title="Example post A", body="Just a test")
      postB = models.Post(title="Example post B", body="Still a test")
      
      session.add_all([postA, postB])
      session.commit()
      
      data = {
        "title": "Example Post",
        "body": 32
      }
      
      response = self.client.post("/api/posts/{}".format(postB.id),
                                 data=json.dumps(data),
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 422)
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "32 is not of type 'string'")
    
    def testEditPostMissingData(self):
      """ Posting a post with a missing body """
      postA = models.Post(title="Example post A", body="Just a test")
      postB = models.Post(title="Example post B", body="Still a test")
      
      session.add_all([postA, postB])
      session.commit()
      
      data = {
        "title": "Example Post",
      }
      
      response = self.client.post("/api/posts/{}".format(postB.id),
                                 data=json.dumps(data),
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 422)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "'body' is a required property")
      

if __name__ == "__main__":
    unittest.main()

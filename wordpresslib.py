"""
    wordpresslib.py

    WordPress xml-rpc client library
    use MovableType API

    Copyright (C) 2005 Michele Ferretti
    black.bird@tiscali.it
    http://www.blackbirdblog.it

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA    02111-1307, USA.

    XML-RPC supported methods:
        * getUsersBlogs
        * getUserInfo
        * getPost
        * getRecentPosts
        * newPost
        * editPost
        * deletePost
        * newMediaObject
        * getCategoryList
        * getPostCategories
        * setPostCategories
        * getTrackbackPings
        * publishPost
        * getPingbacks

    References:
        * http://codex.wordpress.org/XML-RPC_Support
        * http://www.sixapart.com/movabletype/docs/mtmanual_programmatic.html
        * http://docs.python.org/lib/module-xmlrpclib.html
"""

__author__ = "Michele Ferretti <black.bird@tiscali.it>"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2005/05/02 $"
__copyright__ = "Copyright (c) 2005 Michele Ferretti"
__license__ = "LGPL"

import os.path
import time
import xmlrpclib

class WordPressException(Exception):
    """ Custom exception for WordPress client operations """
    def __init__(self, obj):
        if isinstance(obj, xmlrpclib.Fault):
            self.id = obj.faultCode
            self.message = obj.faultString
        else:
            self.id = 0
            self.message = obj

    def __str__(self):
        return '<%s %d: \'%s\'>' % (
                self.__class__.__name__, self.id, self.message)

class WordPressBlog(object):
    """ Represents blog item """
    def __init__(self):
        self.id      = ''
        self.name    = ''
        self.url     = ''
        self.isAdmin = False
        self.xmlrpc  = ''

class WordPressUser(object):
    """ Represents user item """
    def __init__(self):
        self.id        = ''
        self.firstName = ''
        self.lastName  = ''
        self.nickname  = ''
        self.email     = ''

class WordPressCategory(object):
    """ Represents category item """
    def __init__(self):
        self.id          = 0
        self.parentId    = 0
        self.description = ''
        self.name        = ''
        self.html_url    = ''
        self.rss_url     = ''

class WordPressTag(object):
    """ Represents tag item """
    def __init__(self):
        self.id       = ''
        self.name     = ''
        self.count    = 0
        self.slug     = ''
        self.html_url = ''
        self.rss_url  = ''

class WordPressPost(object):
    """ Represents post item """
    def __init__(self):
        self.id            = 0
        self.title         = ''
        self.date          = None
        self.permaLink     = ''
        self.description   = ''
        self.textMore      = ''
        self.excerpt       = ''
        self.link          = ''
        self.categories    = []
        self.tags          = []
        self.user          = ''
        self.allowPings    = False
        self.allowComments = False

class WordPressClient(object):
    """ Client for connect to WordPress XML-RPC interface """

    def __init__(self, url, user, password):
        self.url        = url
        self.user       = user
        self.password   = password
        self.blogId     = 0
        self.categories = None
        self.tags       = None
        self._server    = xmlrpclib.ServerProxy(
            self.url, use_datetime=True)

    def _filterPost(self, post):
        """ Transform post struct in WordPressPost instance """
        postObj               = WordPressPost()
        postObj.permaLink     = post['permaLink']
        postObj.description   = post['description']
        postObj.title         = post['title']
        postObj.excerpt       = post['mt_excerpt']
        postObj.user          = post['userid']
        postObj.date          = time.strptime(
                str(post['dateCreated']), "%Y%m%dT%H:%M:%S")
        postObj.link          = post['link']
        postObj.textMore      = post['mt_text_more']
        postObj.allowComments = post['mt_allow_comments'] == 1
        postObj.id            = int(post['postid'])
        postObj.categories    = post['categories']
        postObj.allowPings    = post['mt_allow_pings'] == 1
        return postObj

    def _filterCategory(self, cat):
        """ Transform category struct in WordPressCategory instance """
        catObj      = WordPressCategory()
        catObj.id   = int(cat['categoryId'])
        catObj.parentId = int(cat['parentId'])
        catObj.description = cat['description']
        catObj.name = cat['categoryName']
        catObj.html_url = cat['htmlUrl']
        catObj.rss_url = cat['rssUrl']
        return catObj

    def _filterTag(self, tag):
        """ Transform tag struct in WordPressTag instance """
        tagObj          = WordPressTag()
        tagObj.id       = int(tag['tag_id'])
        tagObj.name     = tag['name']
        tagObj.count    = tag['count']
        tagObj.slug     = tag['slug']
        tagObj.html_url = tag['html_url']
        tagObj.rss_url  = tag['rss_url']
        return tagObj

    def selectBlog(self, blogId):
        self.blogId = blogId
        found = False
        for blog in self.getUsersBlogs():
            if blogId == blog.id:
                self.blogId  = blogId
                self.url     = blog.xmlrpc
                self._server = xmlrpclib.ServerProxy(
                    self.url, use_datetime=True)
                found = True

        if not found:
            raise WordPressException('Blog not found')

    def supportedMethods(self):
        """ Get supported methods list """
        return self._server.mt.supportedMethods()

    def getLastPost(self):
        """ Get last post """
        return tuple(self.getRecentPosts(1))[0]

    def getRecentPosts(self, numPosts=5):
        """ Get recent posts """
        try:
            posts = self._server.metaWeblog.getRecentPosts(
                    self.blogId, self.user, self.password, numPosts)
            for post in posts:
                yield self._filterPost(post)
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getPost(self, postId):
        """ Get post item """
        try:
            return self._filterPost(
                    self._server.metaWeblog.getPost(
                            str(postId), self.user, self.password))
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getUserInfo(self):
        """ Get user info """
        try:
            userinfo = self._server.blogger.getUserInfo(
                    '', self.user, self.password)
            userObj           = WordPressUser()
            userObj.id        = userinfo['userid']
            userObj.firstName = userinfo['firstname']
            userObj.lastName  = userinfo['lastname']
            userObj.nickname  = userinfo['nickname']
            userObj.email     = userinfo['email']
            return userObj
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getUsersBlogs(self):
        """ Get blog's users info """
        try:
            blogs = self._server.wp.getUsersBlogs(self.user, self.password)
            for blog in blogs:
                blogObj         = WordPressBlog()
                blogObj.id      = blog['blogid']
                blogObj.name    = blog['blogName']
                blogObj.isAdmin = blog['isAdmin']
                blogObj.url     = blog['url']
                blogObj.xmlrpc  = blog['xmlrpc']
                yield blogObj
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def newPost(self, post, publish):
        """ Insert new post """
        blogContent = {
            'title' : post.title,
            'description' : post.description,
            'mt_keywords': post.tags,
        }

        if post.date is not None:
            blogContent['dateCreated'] = post.date

        # add categories
        categories = []
        for cat in post.categories:
            categories.append({'categoryId' : cat, 'isPrimary': 0})

        # insert new post
        idNewPost = int(
                self._server.metaWeblog.newPost(
                        self.blogId, self.user, self.password, blogContent, 0))

        # set categories for new post
        self.setPostCategories(idNewPost, categories)

        # publish post if publish set at True
        if publish:
            self.publishPost(idNewPost)

        return idNewPost

    def getPostCategories(self, postId):
        """ Get post's categories """
        try:
            categories = self._server.mt.getPostCategories(
                    postId, self.user, self.password)
            for cat in categories:
                yield self._filterCategory(cat)
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def setPostCategories(self, postId, categories):
        """ Set post's categories """
        self._server.mt.setPostCategories(
                postId, self.user, self.password, categories)

    def editPost(self, postId, post, publish):
        """ Edit post """
        blogcontent = {
            'title'          : post.title,
            'description'    : post.description,
            'permaLink'      : post.permaLink,
            'mt_allow_pings' : post.allowPings,
            'mt_text_more'   : post.textMore,
            'mt_excerpt'     : post.excerpt
        }

        if post.date:
            blogcontent['dateCreated'] = xmlrpclib.DateTime(post.date)

        # add categories
        categories = []
        for cat in post.categories:
            categories.append({'categoryId' : cat, 'isPrimary': 0})

        result = self._server.metaWeblog.editPost(
                postId, self.user, self.password, blogcontent, 0)

        if result == 0:
            raise WordPressException('Post edit failed')

        # set categories for new post
        self.setPostCategories(postId, categories)

        # publish new post
        if publish:
            self.publishPost(postId)

    def deletePost(self, postId):
        """ Delete post """
        try:
            return self._server.blogger.deletePost(
                    '', postId, self.user, self.password)
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getTags(self):
        """ Get blog's tag list """
        try:
            if not self.tags:
                self.tags = []
                tags = self._server.wp.getTags(
                    self.blogId, self.user, self.password)
                for tag in tags:
                    self.tags.append(self._filterTag(tag))

            return self.tags
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getCategories(self):
        """ Get blog's categories list """
        try:
            if not self.categories:
                self.categories = []
                categories = self._server.wp.getCategories(
                        self.blogId, self.user, self.password)
                for cat in categories:
                    self.categories.append(self._filterCategory(cat))

            return self.categories
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getCategoryIdFromName(self, name):
        """ Get category id from category name """
        for c in self.getCategories():
            if c.name == name:
                return c.id

    def getTrackbackPings(self, postId):
        """ Get trackback pings of post """
        try:
            return self._server.mt.getTrackbackPings(postId)
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def publishPost(self, postId):
        """ Publish post """
        try:
            return (self._server.mt.publishPost(
                            postId, self.user, self.password) == 1)
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def getPingbacks(self, postUrl):
        """ Get pingbacks of post """
        try:
            return self._server.pingback.extensions.getPingbacks(postUrl)
        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

    def newMediaObject(self, mediaFileName):
        """ Add new media object (image, movie, etc...) """
        try:
            f = file(mediaFileName, 'rb')
            mediaBits = f.read()
            f.close()

            mediaStruct = {
                'name' : os.path.basename(mediaFileName),
                'bits' : xmlrpclib.Binary(mediaBits)
            }

            result = self._server.metaWeblog.newMediaObject(
                    self.blogId, self.user, self.password, mediaStruct)
            return result['url']

        except xmlrpclib.Fault, fault:
            raise WordPressException(fault)

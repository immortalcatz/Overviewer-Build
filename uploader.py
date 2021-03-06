import urllib2
import subprocess
import os
import stat

class Uploader:
    def popen(self, action, cmd):
        #self.logger.info("running command [%s]" % action)
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            #self.logger.error("Error during [%s]" % action)
            raise Exception()
    
    def check_exists(self, path):
        """Returns true if the given file already exists."""
        raise NotImplementedError()
    def get_url(self, path):
        """Returns the URL associated with the given path."""
        raise NotImplementedError()
    def upload(self, path, srcfile):
        """Upload the file located at srcfile to path, and return the
        access URL."""
        raise NotImplementedError()

class S3Uploader(Uploader):
    def __init__(self):
        try:
            import boto
        except ImportError:
            import sys
            sys.path.append(r"c:\devel\boto")
            import boto
            
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key
        
        self.conn = S3Connection('1QWAVYJPN7K868CEDZ82')
        self.bucket = self.conn.get_bucket("minecraft-overviewer")

    def check_exists(self, path):
        k = self.bucket.get_key(path)
        if k:
            return True
        return False
    
    def get_url(self, path):
        return "https://s3.amazonaws.com/minecraft-overviewer/%s" % path
    
    def upload(self, path, srcfile):
        k = self.bucket.new_key(path)
        options = {}
        if path.endswith(".txt"):
            options['headers'] = {'Content-Type': 'text/plain'}
        k.set_contents_from_filename(srcfile, **options)
        k.change_storage_class("REDUCED_REDUNDANCY")
        k.make_public()
        
        return self.get_url(path)

class OverviewerOrgUploader(Uploader):
    class HeadRequest(urllib2.Request):
        def get_method(self):
            return "HEAD"
    
    def __init__(self):
        self.baseurl = "http://overviewer.org/builds/"
        self.basedest = "overviewer-upload@overviewer.org:/var/www/org/overviewer/htdocs/builds/"
        self.scp = 'scp'
    
    def check_exists(self, path):
        url = self.baseurl + path
        try:
            response = urllib2.urlopen(self.HeadRequest(url))
            return True
        except urllib2.HTTPError:
            return False
    
    def get_url(self, path):
        return self.baseurl + path
    
    def upload(self, path, srcfile):
        dest = self.basedest + path
        
        # fix access modes so others can read it
        os.chmod(srcfile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        self.popen("scp", [self.scp, srcfile, dest])
        return self.get_url(path)

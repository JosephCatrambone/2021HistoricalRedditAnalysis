#!/usr/bin/env python
# coding: utf-8

# Analyzing Subreddit Data from ~10 Years

# In[13]:


datapath = "/run/user/1000/gvfs/smb-share:server=freenas.local,share=mldata/reddit_data/"


# In[43]:


import gzip
import json
import os
import pickle
import sys
import time
from bz2 import BZ2File
from glob import glob

# In[48]:

def _for_each_comment(all_comment_files, fn, comment_checkpoint, file_checkpoint):
	"""Run 'fn' once with each comment.  
	At the end of running 'fn', call comment_checkpoint with a line number.
	At the end of running a file, call the file_checkpoint.
	"""
	errors = dict()
	for comment_file in all_comment_files:
		print(comment_file)
		fileref = BZ2File(comment_file)
		for linenum, line in enumerate(fileref):
			try:
				comment = json.loads(line)
				fn(comment)
			except InterruptedError:
				break
			except KeyboardInterrupt:
				break
			except Exception as e:
				errors[f"{comment_file}:{linenum}"] = e
			if comment_checkpoint:
				comment_checkpoint(linenum)
		if file_checkpoint:
			file_checkpoint()
	return errors

def for_each_comment(fn, comment_checkpoint=None, file_checkpoint=None):
	all_comment_files = glob(str(os.path.join(datapath, "**", "*.bz2")))
	return _for_each_comment(all_comment_files, fn, comment_checkpoint, file_checkpoint)

def for_each_comment_in_year(year, fn, comment_checkpoint=None, file_checkpoint=None):
	comment_files = glob(str(os.path.join(datapath, "**", f"RC_{year}-*.bz2")))
	return _for_each_comment(comment_files, fn, comment_checkpoint, file_checkpoint)


# In[27]:


user_comments_by_subreddit = dict()  # Map of username -> subreddit comment count
def tally_comment(com):
	username = com.get('author')
	subreddit = com.get('subreddit')
	if username and subreddit:
		if username not in user_comments_by_subreddit:
			user_comments_by_subreddit[username] = dict()
		user_comments_by_subreddit[username][subreddit] = user_comments_by_subreddit[username].get(subreddit, 0)+1


# In[49]:

def main():
	for year in range(2007, 2016):
		# Clear old user comments...
		print(f"Setting up {year}...")
		user_comments_by_subreddit = dict()
		def tally_comment(com):
			username = com.get('author')
			subreddit = com.get('subreddit')
			if username and subreddit:
				if username not in user_comments_by_subreddit:
					user_comments_by_subreddit[username] = dict()
				user_comments_by_subreddit[username][subreddit] = user_comments_by_subreddit[username].get(subreddit, 0)+1
		def sleep_after_5k(line_count):
			if line_count % 5000 == 0:
				time.sleep(0.01)
		def checkpoint():
			print("Saving...")
			with gzip.open(f"reddit_comment_tally_{year}.json.gz", 'wt') as fout:
				json.dump(user_comments_by_subreddit, fout)
		# Process comments for year...
		print("Processing...")
		_ = for_each_comment_in_year(year, tally_comment, comment_checkpoint=sleep_after_5k, file_checkpoint=checkpoint)


if __name__ == "__main__":
	main()


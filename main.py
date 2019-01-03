import json
import requests

from kivy.app import App
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
#TODO: Replace print statements with logging


__version__ = 0.1

class RootWidget(RelativeLayout):
    manager = ObjectProperty(None)
    commits_box = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.commits_box.bind(minimum_height=self.commits_box.setter('height'))

    def fetch_open_pull_requests_by_repo_name(self, username, reponame, debug=False):
    #Obtains a json of pullrequests for a repository under a username
        data = None
        if not debug:
            try:
                response = requests.get('https://api.github.com/repos/' + username + '/' + reponame + '/pulls')
                data = response.json()
            except:
                print('Some bad shit happende while fetching the pull requests by reponame')
        else:
            data = json.load(open('pulls.json', 'r'))
        return data
    
    def extract_pull_requests(self, json_string, debug=False):
    #Obtains a dictionary of pull req title -> created_at, updated_at, base, head
        pull_requests = {}
        try:
            for pr in json_string:
                pull_requests[pr['title']] = \
                {
                    'created_at': pr['created_at'],
                    'updated_at': pr['updated_at'],
                    'base': pr['base']['ref'],
                    'head': pr['head']['ref'],
                }
        except:
            print('No or invalid pull requests')
            pull_requests = {} #cleanup
        return pull_requests

    def fetch_commits_by_repo_name(self, username, reponame, debug=False):
    #Obtains json of commits for a repository of a username
        data = None
        if not debug:
            try:
                response = requests.get('https://api.github.com/repos/' + username + '/' + reponame + '/commits')
                data = response.json()
            except:
                print("Some bad shit happened while fetching commits by repo name")
        else:
            data = json.load(open('commits.json', 'r'))
        return data
    
    def build_repo_dict(self, username, reponame, debug=False):
    #creates a dictionary of repo -> commits, pull request data
        repository_details = {}
        repository_details[reponame] = \
        {
            'commits': self.extract_last_5_commits(self.fetch_commits_by_repo_name(username, reponame, debug)),
            'pull_requests': self.extract_pull_requests(self.fetch_open_pull_requests_by_repo_name(username, reponame, debug))
        }
        return repository_details

    def extract_last_5_commits(self, json_string, debug=False):
    #Parse json string and get back last 5 commits as dict of sha -> message, committer details
        commits = {}
        for commit in json_string[:5]:
            commits[commit['sha']] = \
            {
                'message': commit['commit']['message'],
                'committer': commit['commit']['author']['name'],
                'committer_email': commit['commit']['author']['email'],
                'created_at': commit['commit']['author']['date']
            }
        return commits

    def fetch_user_repo_info(self, username, debug=False):
    #Make a request to github api, convert to json format and return
        data = None
        if not debug:
            try:
                print("gonna try to open this:" + 'https://api.github.com/users/' + username + '/repos')
                response = requests.get('https://api.github.com/users/' + username + '/repos')
                print("I made it to line 97!")
                data = response.json()
                print("I made it to line 99!")
            except:
                print("Some bad shit happened while fetchig user repository info")
        else:
            data = json.load(open('data.json', 'r'))
        return data

    def extract_repositories(self, json_string, debug=False):
    #From obtained json data, select only repository names and return them
                try:
                    return [item['name'] for item in json_string[:]]
                except:
                    self.ids.username_input.text = 'Invalid Username'
                    return []
    def populate_repository_details_screen(self, username, reponame, debug=False):
    #Clear widgets from previous info then repopulated them with labels containing parse info
        repository_info = self.build_repo_dict(username, reponame, debug)
        repository_info = repository_info[reponame]
        self.ids.commits_box.clear_widgets()
        self.ids.pr_box.clear_widgets()

        for sha, dic in repository_info['commits'].items():
            label = Label(text='Message: %s\nAuthor: %s\nEmail: %s\nCreated At: %s' %
                                                         (dic['message'].strip(),
                                                          dic['committer'].strip(),
                                                          dic['committer_email'].strip(),
                                                          dic['created_at'].strip()
                                                         )
                         )
            label.text_size = self.width, None
            self.ids.commits_box.add_widget(label)
        
        for title, dic in repository_info['pull_requests'].items():
            label = Label(text='\nTitle: %s\nBase: %s\nHead: %s\nCreated At: %s\nUpdated At: %s\n' %
                            (title,
                             dic['base'],
                             dic['head'],
                             dic['created_at'],
                             dic['updated_at']
                            ),
                         )
            # label.text_size = (label.width, None)
            # label.size_hint = (1, None)

        self.manager.current = 'details'

    def populate_repository_screen(self, username, debug=False):
    #Get repositories associated with username, create buttons for each of them
        self.ids.repo_list.clear_widgets()
        repositories_list = self.extract_repositories(self.fetch_user_repo_info(username,debug=debug), debug=debug)
        if not len(repositories_list):
            print("There are no repositories for this username")
            return
        for repo in repositories_list:
            self.ids.repo_list.add_widget(Button(text=repo, on_release=lambda _, repo=repo: self.populate_repository_details_screen(username, repo)))
        
        self.manager.current = "repos"
        

class VcApp(App):


    def build(self):
        print("Im starting some shit")
        return RootWidget()

if __name__ == '__main__':
    VcApp().run()

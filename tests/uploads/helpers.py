import boto3, botocore
from .config import S3_KEY, S3_SECRET, S3_BUCKET, S3_LOCATION, GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_PASSWORD 
from github import Github
from github import InputGitTreeElement
from git import Repo
from pprint import pprint
import time
import os

s3 = boto3.client(
   "s3",
   region_name="us-east-1",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)

notifier = boto3.client(
    "sns",
    region_name="us-east-1",
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET
)

git = Github(login_or_token=GITHUB_TOKEN)
# git = Github(login_or_token=GITHUB_USERNAME, password=GITHUB_PASSWORD) # deprecated way of accessing

def send_message_to_phone(phone, path):
    message = "Your upload is successful, and the url is " + path

    response = notifier.publish(
        PhoneNumber=str(phone), Message=message,
        MessageAttributes = {
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'  # 'Promotional' or 'Transactional'
            }
        }
    )
    print("Response from sms: ", response)

def delete_branch(branchname):
    repo = git.get_user().get_repo("4156-test-upload")
    # repo = git.get_user().get_repo("gzhami/research_lab")
    
    src = repo.get_git_ref("heads/"+branchname)
    response = src.delete()
    print(response)

def merge_branch(branch_name, commit_message="merge", base="main"):
    try:
        # base = repo.get_branch(base)
        repo = git.get_user().get_repo("4156-test-upload")
        head = repo.get_branch(branch_name)

        merge_to_master = repo.merge(base,
                            head.commit.sha, commit_message)
        pprint(merge_to_master)
    except Exception as ex:
        print(ex)

def test_github(file, new_branch, user_id):
    repo = git.get_user().get_repo("4156-test-upload")
    pprint(list(repo.get_branches()))
    # user_id = str("linxiaow") # use timestamp for now
    # snew_branch = str(user_id+"/test8")
    commit_message = "test commit"

    source_branch = 'main'
    # target_branch = 'test'

    sb = repo.get_branch(source_branch)
    ret = repo.create_git_ref(ref='refs/heads/' + new_branch, sha=sb.commit.sha)
    pprint(ret)

    filename = "strategy3.py"
    filepath = os.path.join(user_id, filename)
    repo.create_file(filepath, commit_message, file.read(), new_branch)

    # file_name = "test.py"
    # commit_message = 'python update 2'
    # master_ref = repo.get_git_ref('heads/master')
    # master_sha = master_ref.object.sha
    # base_tree = repo.get_git_tree(master_sha)
    # element_list = list()
    # element = InputGitTreeElement(file_name, '100644', 'blob', file)
    # element_list.append(element)
    # tree = repo.create_git_tree(element_list, base_tree)
    # parent = repo.get_git_commit(master_sha)
    # commit = repo.create_git_commit(commit_message, tree, [parent])
    # master_ref.edit(commit.sha)
    github_prefix = "" # need to fix
    return filepath


def upload_file_to_s3(file, bucket_name, acl="public-read"):
    '''
    Notice that, in addition to ACL we set the ContentType key in ExtraArgs to the file's content type. This is because by default, all files uploaded to an S3 bucket have their content type set to binary/octet-stream, forcing the browser to prompt users to download the files instead of just reading them when accessed via a public URL (which can become quite annoying and frustrating for images and pdfs for example)
    '''
    upload_path = "uploads/" + file.filename
    try:
        print("uploading file: ", file.filename)
        # with open(file.filename, 'rb') as data:
        s3.upload_fileobj(
            file,
            bucket_name,
            upload_path,
            # ExtraArgs={
            #     "ACL": acl,
            #     "ContentType": file.content_type
            # }
        )

    except Exception as e:
        # This is a catch all exception, edit this part to fit your needs.
        print("Something Happened: ", e)
        return e

    # return "{}{}".format(app.config["S3_LOCATION"], file.filename)
    return "{}{}".format(S3_LOCATION, upload_path)

import git
from github import Github
import os
import subprocess
import shutil
import re

def count_lines_code(repo_path):
#     Counts the total number of lines of code in a given repository.
#
#     Args:
#         repo_path (str): The path to the local repository.
#
#     Returns:
#         int: The total number of lines of code in the repository.

    total_lines = 0
    # List of valid extensions
    extensions = ['.js', '.ts', '.jsx', '.tsx', '.sh', '.md', '.yaml', '.yml', '.json', 
    '.xml', '.html', '.css', '.scss', '.less', '.php', '.py', '.go', '.java', '.rb', 
    '.pl', '.pm', '.pp', '.swift']
    try:
        # Change the working directory to the repository path.
        os.chdir(repo_path)
        # Run a git command to get a list of all files in the repository.
        cmd = f'git ls-tree --name-only -r HEAD {repo_path}'
        output = subprocess.check_output(cmd.split(), stderr=subprocess.PIPE).decode().split('\n')

        # Iterate over each file in the output and count the lines of code if the file extension is in the extensions list.
        for file in output:
            if os.path.isfile(file) and os.path.splitext(file)[1] in extensions:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
#                     print(f"{file}: {len(lines)} lines")
                    total_lines += len(lines)
#         print(total_lines)
        return total_lines
    except subprocess.CalledProcessError:
        # If an error occurs, delete the repository path and return 0.
        shutil.rmtree(repo_path, ignore_errors=True)
        return 0

def super_lint(repo_url, pat):
#     Runs the GitHub Super-linter on a GitHub repository and returns a score 
#     based on the number of errors.
#
#     Args:
#         repo_url (str): The URL of the GitHub repository.
#         pat (str): The personal access token for the GitHub API.
#
#     Returns:
#         float: A score between 0 and 1, where 1 is no errors and 0 is all errors.

    # Use a regular expression to extract the username and repository name from the URL.
    match = re.match(r"https://github.com/([\w-]+)/([\w-]+)", repo_url)
    if match:
        username = match.group(1)
        repo_name = match.group(2)
#         print(f"Username: {username}")
#         print(f"Repository name: {repo_name}")
    else:
        # print("Invalid GitHub URL.")
        return 0
    
    # Use the username, repository name, and personal access token to create a Git URL.
    repo_url = f'https://{username}:{pat}@github.com/{username}/{repo_name}.git'
    
    # Gets the current working directory
    cwd = os.getcwd()

    tmp_repo_path = 'tmp_repo'

    try:
        # Clone the repository to a temporary path or fetch updates if it already exists.
        if not os.path.exists(tmp_repo_path):
            git.Repo.clone_from(repo_url, tmp_repo_path)
        else:
            repo = git.Repo(tmp_repo_path)
            origin = repo.remote(name='origin')
            origin.fetch()
    except:
        # If an error occurs, return 0
#         print("Either PAT is invalid or repository does not exist.")
        return 0
    # Count the number of lines of code in the repository. Return 0 if
    # number of lines is zero
    os.chdir(tmp_repo_path)
    lines_of_code = count_lines_code(f'{cwd}/{tmp_repo_path}')
    if lines_of_code == 0:
        return 0
    # Return to the root directory
    os.chdir(cwd)
    # Run the GitHub Super-Linter
    output = subprocess.run(['sudo', 'docker', 'run', '--rm', '-e', 'RUN_LOCAL=true', '-v', f'{cwd}/{tmp_repo_path}:/tmp/lint', f'github/super-linter'], 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Delete the temporary repository directory
    shutil.rmtree(f'{cwd}/{tmp_repo_path}', ignore_errors=True)

    output = output.stderr.decode()
    error_count = 0
    script_completed = False
    output = output.splitlines()
    # If the script has completed, check the number of errors and return it
    for line in output:
        if not script_completed:
            if 'The script has completed' in line:
                script_completed = True
        else:
            if '[ERROR]' in line:
                error_count += 1
    
    return 1 - (error_count / lines_of_code)


def lines_per_pull(repo_url, pat):
#     Calculates the average number of lines changed per pull request for a GitHub repository.
#
#     Parameters:
#     repo_url (str): The URL of the GitHub repository in the format 'https://github.com/username/repo'.
#     pat (str): The personal access token (PAT) for authentication.
#
#     Returns:
#     float: The average number of lines changed per pull request. Returns 0 if there are no pull requests or if the URL/PAT is invalid.

    # Uses a regular expresion to verify the format of the URL
    # and extract the username and repository name
    match = re.match(r"https://github.com/([\w-]+)/([\w-]+)", repo_url)
    if match:
        username = match.group(1)
        repo_name = match.group(2)
#         print(f"Username: {username}")
#         print(f"Repository name: {repo_name}")
    else:
        # print("Invalid GitHub URL.")
        return 0
    # Combines the username and repository name into the path
    repo_name = f'{username}/{repo_name}'
    # Authenticates to GitHub using the Personal Access Token
    github = Github(pat)
    try:
        # Get the repository from GitHub
        repo = github.get_repo(repo_name)
    except:
        # If it fails, return the number of lines as 0
#         print("Either PAT is invalid or repository does not exist.")
        return 0
    total_lines_changed = 0
    num_pulls = 0
    # Loop through all pull requests in the repository
    for pull in repo.get_pulls(state='all'):
        num_lines_changed = 0
        # Loop through each file in the pull request and add the total number of
        # lines added and removed from the file to the total 
        for file in pull.get_files():
            num_lines_changed += file.additions + file.deletions
        total_lines_changed += num_lines_changed
        num_pulls += 1
    # If there have been pull requests, return the average number of lines per PR 
    if (num_pulls != 0):
        avg_lines_changed = total_lines_changed / num_pulls
        return avg_lines_changed
    else:
        # Otherwise, return 0
#         print("There have been no pull requests!")
        return 0

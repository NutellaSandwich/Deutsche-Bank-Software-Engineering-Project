# Installation
- NOTE: This system is currently only supported/tested on a fresh install of Ubuntu however it has been successfully installed on MacOS
- First clean your installation directory using the `sudo ./clean.sh` command.
- Then run `sudo ./setup.sh` command to initialise the virtual environment and install the given requirements (specified in requiresments.txt)
- To run the flask server use the `sudo ./run.sh` command.

- You will need to update the .env file with the Flask app secret key. This can be done by adding the following line:
- SECRET_KEY=<your string>,
  where <your string> is your secret key for the server

# Git/GitHub
GitHub is a online version control and code repository sharing platform. It is very useful for collaborative development. I suggest you become very familar with the basics you need, all briefly mentioned here. If you need more of a tutorial, here are some suggested resources:
- https://product.hubspot.com/blog/git-and-github-tutorial-for-beginners.
- https://medium.com/it-developers/git-tutorial-for-beginners-remote-repository-management-490fa4937fab
- https://thenewstack.io/dont-mess-with-the-master-working-with-branches-in-git-and-github/


## Getting started
First you will need to create an empty local repository on your machine (I highly recommend using the DCS systems for ease of compatibility).

In your terminal, go to your cs261 directory and create a new `groupproject` directory using `mkdir groupproject`.

Then `cd grouproject` to change into that newly created directory.

Then run `git init` - this will initialise an empty git repo in the directory.

Then rename the current branch to main using `git branch -M main`.

It is useful to create a short hand name for the remote repo. You can do this with the following command:
`git remote add origin https://github.com/MikeCooper18/cs261.git`
This gives the remote repo the short name `origin`.


## Branches
Rule 1: **NEVER** make changes directly to the main branch. Create a new branch and then merge as needed.

Essentially a branch is an alternative version of a code base which you can make changes to, **without** affecting the other branches.
This is particularly useful for Software Engineering when implementing new features or fixing bugs. You can create a new branch, do what you need, and when you're certain it works as expected you can combine that new modified branch into another branch using a merge.

To list branches use the `git branch -a` command.


To create a branch use the `git branch <branchName>` command.

To move to a branch, use the `git checkout <branchName>` command.

Any commits you then make, via `git commit -m "<message>"`, will only affect that branch.


## Making Changes
In a git repo you must *stage* the changes you make. This is a fancy name for tell git to track a certain file(s).

To do this, use the `git add <file pattern>` command. The `<file pattern>` can be one of many things, an individual filename, a folder or a regex pattern specifying all files/folders to match.

Most commonly, you will need to use the `git add --all`, this stages all files in the git repo which have been changed, excluding the files specified in the `.gitignore` file.

Once the changes are staged, you must then *commit* or save the changes. This is done using the command `git commit -m "<commit message>"`, and will commit all staged changes to the current branch.


## Merging
Once you are done making changes (and committing) on a branch and you are certain it works/passes all tests, you can combine the changes on that branch with the main branch.
First make sure you are on the main branch using `git checkout main` (or the branch you want to merge **to** `git checkout <branch name>`).

Check which branch you are on using the `git branch` command. The branch you are currently on has a `*` by its name.
Then use the command `git merge <branch name> --no-ff` command. This merges `<branch name>` onto the branch you are current in.

Once a git branch has been merged, and you are certain you no longer need that branch, you can delete the branch using `git branch -d <branch name>`.


## Pulling
Pulling is the process of getting the code from the remote repo and saving it to your local repo.
To pull the changes from the remote repo, use `git pull origin main`.

## Pushing
To push or save your changes in your local repo to the remote repo you can run the following command.
`git push https://github.com/MikeCooper18/cs261.git main`
or as shorthand: `git push origin main`.

## Remarks
A few other useful commands:
- `git log` will print out a log of all of the commits which have occured. I personally use the command with the following additional flags `git log --graph --all`.
- `git status` will show you information about the current branch you are working on, including name, staged changes and unstaged changes.

And finally, the most important (but hopefully never needed) resource: https://dangitgit.com/en.

If the command line seems scary. Visual Studio Code has a handy interface for interacting with a remote GitHub repo. I suggest you install the extension if required (feel free to ask Michael if you want a quick tutorial on this).



# Helpful
## Database manipulation
- More comprehensive documentation here: https://sqlite.org/cli.html
- There is some template data in the `db_init()` function in the `db_schema.py` file. This data can be inserted into the database by changing the `resetdb` boolean to `True` in the `cwk.py` file.
- You can view the data in the database by clicking on the `database.sqlite` file in VS Code. This should open a window where you can view each table. (Might need to install an extension).
- You can open up the interactive database command line by typing `sqlite3 database.sqlite` in the command line in the directory the database is in. To exit this interactive command line press `Ctrl+D`.
- When in the interactive database command line here are a few useful commands:
  - `.tables` - lists all tables in the database.
  - `select * from <tablename>;` - print all rows in table.

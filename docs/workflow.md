# Workflow

## Changelog

(2020-11-29) default branch has been changed from `master` to `dev`. In addition, both `dev` and `master` are protected 
so that force push or push directly to either branch is strictly forbidden.

## Readings

1. [Git Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
2. [Best Practice for Protected Branch](https://github.community/t/best-practices-for-protected-branches/10204)
3. [Prevent pushing directly to master](https://stackoverflow.com/questions/46146491/prevent-pushing-to-master-on-github)


## Workflow

1. use `feature/feature-name`, `hotfix/hot-fix-name`, `debug/debug-name` to name your branch. Avoid naming your branch 
at root level.
2. create a pull request by pushing to a remote branch first.
3. get 1 approval at least before merging to `dev`
4. when `merged` into `dev` branch, AWS CodePipeline will automatically pick up the code change to deploy our change
to a testnet (hosted on Elastic Beanstalk). Having a test-net empowers us from deploying unintended code that could 
potentially cause breakages.
5. when verified that testnet appears working without errors, an admin will deploy the code from `dev` to `master` and 
upon merging the code, a similar CodePipeline will pick up the new code and deploy to our main-net.

## Protected Branch

* `dev` is protected to all users including admins.
* `master` is also protected to all users including admins.

### example of illegal push actions

Here, I tried to push directly to master from master branch. It would forbids me.

```
└─ $ ▶git push
Enumerating objects: 8, done.
Counting objects: 100% (8/8), done.
Delta compression using up to 16 threads
Compressing objects: 100% (5/5), done.
Writing objects: 100% (5/5), 554 bytes | 554.00 KiB/s, done.
Total 5 (delta 3), reused 0 (delta 0)
remote: Resolving deltas: 100% (3/3), completed with 3 local objects.
remote: error: GH006: Protected branch update failed for refs/heads/master.
remote: error: Required status check "build-linux" is expected. At least 1 approving review is required by reviewers with write access.
To https://github.com/gzhami/research_lab.git
 ! [remote rejected] master -> master (protected branch hook declined)
error: failed to push some refs to 'https://github.com/gzhami/research_lab.git'
```

Instead, I should do this

```
└─ $ ▶git push origin local_branch:doc/update-docs
Enumerating objects: 16, done.
Counting objects: 100% (16/16), done.
Delta compression using up to 16 threads
Compressing objects: 100% (13/13), done.
Writing objects: 100% (13/13), 1.66 KiB | 1.66 MiB/s, done.
Total 13 (delta 9), reused 0 (delta 0)
remote: Resolving deltas: 100% (9/9), completed with 3 local objects.
remote: 
remote: Create a pull request for 'doc/update-docs' on GitHub by visiting:
remote:      https://github.com/gzhami/research_lab/pull/new/doc/update-docs
remote: 
To https://github.com/gzhami/research_lab.git
 * [new branch]      local_branch -> doc/update-docs
```



# Workflow

## Changelog

(2020-11-29) default branch has been changed from `master` to `dev`. In addition, both `dev` and `master` are protected 
so that force push or push directly to either branch is strictly forbidden.

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
## Commit messages
Commit messages should follow the [Conventional Commits Specification](https://www.conventionalcommits.org/en/v1.0.0/#specification) and be written in the _imperative mood_.
* The commit message should be structured as follows:
  ```
  <type>[optional scope]: <brief description>

  [optional detailed description]

  [optional footer(s)]
  ```
* Commit messages should contain an issue ticket in its detailed description
  ```
  feat: add monthly payment endpoint

  Closes #42
  ```
* Main types description:
  * feat: A new feature
  * fix: A bug fix
  * refactor: A code change that neither fixes a bug nor adds a feature
  * test: Adding missing tests or correcting existing tests
  * style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
  * perf: A code change that improves performance
  * docs: Documentation only changes
  * build: Changes that affect the build system or external dependencies
  * ci: Changes to our CI configuration files and scripts
* E.g.:
  * Preferred: `feat: add model validation`, than: `added new feature for model validation. Minor changes`
  * Preferred: `refactor(execution): improve code readability`, than: `refactored execution module to improve code readability`

## Pull Request title
Pull request titles **must** follow [Conventional Commits Specification](#commit-messages) 
above because default and only merge strategy is Squashing with defaulting message to Pull Request title.
If you are lazy enough you can ignore commit messages themselves - 
at the end everything is squashed to a single commit with PR title's message.

## Branch naming
* Branch name should have a specifying prefix with `/`, e.g. `feature/`, `hotfix/`, `chore/`
* Branch name must have a short, actionable descriptor, e.g. `monthly-payment`, `loan-calculator`
* Branch name should have an issue number suffix after `#`, e.g. `feature/monthly-payment#42`
* Use kebab-case naming convention between words
* E.g.:
  * Preferred: `feature/user-authentication#42`, than: `42_new_user_authentication`
  * Preferred: `chore/readme-extension`, than: `chore_readme_extension`
  * Preferred: `hotfix/api-middleware`, than: `fix-api-exceptions-handling-for-user`

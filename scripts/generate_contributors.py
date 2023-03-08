import requests

# Set the repository name and owner
repo_owner = "epam"
repo_name = "badgerdoc"

# Send a GET request to the GitHub API to get the list of contributors
response = requests.get(
    f"https://api.github.com/repos/{repo_owner}/{repo_name}/contributors"
)

# Parse the JSON response
contributors = response.json()

# Generate the markdown-formatted list of contributors
markdown_list = "## Contributors\n\n"
for contributor in contributors:
    markdown_list += f"- [{contributor['login']}](@{contributor['login']})\n"

# Print the markdown list
print(markdown_list)

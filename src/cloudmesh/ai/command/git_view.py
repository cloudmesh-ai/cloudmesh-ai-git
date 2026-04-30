import json
import webbrowser
from pathlib import Path


class GitInfoView:
    """
    Handles the generation and display of the HTML view for Git repository statistics.
    """

    def __init__(self, all_user_data, excludes=None):
        self.all_user_data = all_user_data
        self.excludes = excludes or []

    def generate_html(self):
        """
        Generates a standalone HTML page for viewing repository statistics.
        """
        data_json = json.dumps(self.all_user_data)
        excludes_json = json.dumps(self.excludes)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloudmesh Git Info View</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f6f8fa; color: #24292f; margin: 0; padding: 20px; height: 100vh; box-sizing: border-box; overflow: hidden; }}
        .container {{ width: 100%; margin: 0 auto; height: 100%; display: flex; flex-direction: column; }}
        header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-shrink: 0; }}
        h1 {{ font-size: 24px; font-weight: 600; }}
        #search {{ padding: 8px 12px; width: 300px; border: 1px solid #d0d7de; border-radius: 6px; font-size: 14px; }}
        .user-section {{ margin-bottom: 40px; }}
        .user-header {{ font-size: 20px; font-weight: 600; border-bottom: 2px solid #d0d7de; padding-bottom: 8px; margin-bottom: 15px; color: #0969da; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d0d7de; border-radius: 6px; overflow: hidden; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #d0d7de; font-size: 14px; }}
        th {{ background-color: #f6f8fa; font-weight: 600; }}
        tr:hover {{ background-color: #fcfcfc; }}
        .repo-link {{ color: #0969da; text-decoration: none; font-weight: 600; }}
        .repo-link:hover {{ text-decoration: underline; }}
        .badge {{ display: inline-block; padding: 2px 8px; font-size: 12px; border-radius: 12px; background: #eff1f3; color: #57606a; border: 1px solid #d0d7de; }}
        .stat {{ font-size: 12px; color: #57606a; margin-right: 10px; }}
        .exclude-info {{ font-size: 12px; color: #57606a; margin-bottom: 10px; flex-shrink: 0; display: flex; align-items: center; gap: 10px; }}
        #exclude-input {{ padding: 4px 8px; width: 400px; border: 1px solid #d0d7de; border-radius: 4px; font-size: 12px; }}
        .col-stats {{ width: 300px; }}
        #content {{ flex: 1; overflow-y: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Cloudmesh Git Info View</h1>
            <input type="text" id="search" placeholder="Search repositories..." onkeyup="filterRepos()">
        </header>
        <div class="exclude-info">
            <strong>Exclusions:</strong>
            <input type="text" id="exclude-input" placeholder="Comma separated exclusions..." value="{', '.join(self.excludes) if self.excludes else ''}" onkeyup="filterRepos()">
        </div>
        <div id="content"></div>
    </div>

    <script>
        const data = {data_json};
        
        function render() {{
            const content = document.getElementById('content');
            content.innerHTML = '';
            
            for (const [user, repos] of Object.entries(data)) {{
                const section = document.createElement('div');
                section.className = 'user-section';
                section.dataset.user = user;
                
                let html = `<div class="user-header">${{user}}</div>`;
                html += `<table>
                    <thead>
                        <tr>
                            <th>Org</th>
                            <th>Repo</th>
                            <th>Description</th>
                            <th>PRs</th>
                            <th class="col-stats">Stats</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                repos.forEach(repo => {{
                    const [org, repoName] = repo.repo.split('/');
                    const prs = repo.pull_requests || 0;
                    
                    const stats = [];
                    if (repo.branches) stats.push(`Branches: ${{repo.branches}}`);
                    if (repo.tags) stats.push(`Tags: ${{repo.tags}}`);
                    if (repo.issues) stats.push(`Issues: ${{repo.issues}}`);
                    if (repo.contributors) stats.push(`Contribs: ${{repo.contributors}}`);
                    if (repo.release_version) stats.push(`Rel: ${{repo.release_version}}`);
                    
                    html += `
                        <tr class="repo-row" data-name="${{repo.repo.toLowerCase()}}">
                            <td>${{org}}</td>
                            <td><a href="${{repo.url}}" target="_blank" class="repo-link">${{repoName}}</a></td>
                            <td>${{repo.description || 'No description'}}</td>
                            <td>${{prs}}</td>
                            <td class="col-stats">${{stats.map(s => `<span class="stat">${{s}}</span>`).join('')}}</td>
                            <td>${{repo.last_push ? repo.last_push.split(' ')[0] : 'N/A'}}</td>
                        </tr>`;
                }});
                
                html += `</tbody></table>`;
                section.innerHTML = html;
                content.appendChild(section);
            }}
        }}

        function filterRepos() {{
            const query = document.getElementById('search').value.toLowerCase();
            const excludeValue = document.getElementById('exclude-input').value.toLowerCase();
            const exclusions = excludeValue.split(',').map(s => s.trim()).filter(s => s !== '');
            
            const rows = document.querySelectorAll('.repo-row');
            rows.forEach(row => {{
                const name = row.dataset.name;
                const matchesSearch = name.includes(query);
                const isExcluded = exclusions.some(ex => name.includes(ex));
                
                row.style.display = (matchesSearch && !isExcluded) ? '' : 'none';
            }});
            
            document.querySelectorAll('.user-section').forEach(section => {{
                const visibleRows = section.querySelectorAll('.repo-row[style=""]');
                section.style.display = visibleRows.length > 0 ? '' : 'none';
            }});
        }}

        render();
    </script>
</body>
</html>
"""
        return html

    def open_in_browser(self):
        """
        Saves the HTML to a temporary file and opens it in the browser.
        """
        html_content = self.generate_html()
        temp_file = Path("/tmp/cloudmesh_git_info.html")
        temp_file.write_text(html_content, encoding="utf-8")
        webbrowser.open(f"file://{temp_file.absolute()}")
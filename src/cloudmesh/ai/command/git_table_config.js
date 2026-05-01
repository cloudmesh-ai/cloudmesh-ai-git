window.GitTableConfig = {
    formatSize: function(s) {
        if (!s) return 'N/A';
        if (s > 1024 * 1024) return (s / (1024 * 1024)).toFixed(2) + ' GB';
        if (s > 1024) return (s / 1024).toFixed(2) + ' MB';
        return s + ' KB';
    },

    humanizeDate: function(dateStr) {
        if (!dateStr) return 'N/A';
        const date = new Date(dateStr.split(' ')[0]);
        if (isNaN(date.getTime())) return dateStr;
        
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'just now';
        const minutes = Math.floor(diffInSeconds / 60);
        if (minutes < 60) return minutes + 'm ago';
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return hours + 'h ago';
        const days = Math.floor(hours / 24);
        if (days < 30) return days + 'd ago';
        const months = Math.floor(days / 30);
        if (months < 12) return months + 'mo ago';
        const years = Math.floor(days / 365);
        return years + 'y ago';
    },

    getColumns: function() {
        return [
            { title: "Status", field: "downloaded", width: 60, hozAlign: "center", formatter: function(cell) {
                const val = cell.getValue();
                return `<span class="status-circle ${val ? 'status-downloaded' : 'status-not-downloaded'}"></span>`;
            }},
            { title: "Org", field: "repo", width: 120, formatter: function(cell) {
                const owner = cell.getValue().split('/')[0];
                return `<a href="https://github.com/${owner}" target="_blank" class="repo-link">${owner}</a>`;
            }},
            { title: "Repo", field: "repo", width: 200, formatter: function(cell) {
                const full = cell.getValue();
                const name = full.split('/')[1];
                return `<a href="https://github.com/${full}" target="_blank" class="repo-link">${name}</a>`;
            }},
            { title: "Description", field: "description", formatter: function(cell) {
                return cell.getValue() || 'No description';
            }},
            { title: "Exclude", field: "exclude", width: 120, editor: "input" },
            { title: "Search", field: "search", width: 120, editor: "input" },
            { title: "PRs", field: "pull_requests", width: 80, hozAlign: "center" },
            { title: "Stats", field: "stats", width: 300, formatter: function(cell) {
                const repo = cell.getData();
                const stats = [];
                if (repo.branches) stats.push(`Branches: ${repo.branches}`);
                if (repo.tags) stats.push(`Tags: ${repo.tags}`);
                if (repo.issues) stats.push(`Issues: ${repo.issues}`);
                if (repo.contributors) stats.push(`Contribs: ${repo.contributors}`);
                if (repo.release_version) stats.push(`Rel: ${repo.release_version}`);
                return stats.map(s => `<span class="stat-badge">${s}</span>`).join('');
            }},
            { title: "Size", field: "size", width: 100, hozAlign: "right", formatter: (cell) => GitTableConfig.formatSize(cell.getValue()) },
            { title: "Last Updated", field: "last_push", width: 150, formatter: (cell) => GitTableConfig.humanizeDate(cell.getValue()) },
            { title: "Actions", field: "actions", width: 150, hozAlign: "center", formatter: function(cell) {
                const repo = cell.getData();
                return `
                    <div class="action-icons">
                        <i class="fa-solid fa-rotate" title="Refresh Repo" onclick="refreshRow(repo)"></i>
                        <i class="fa-solid fa-download" title="Download" onclick="downloadRepo('${repo.repo}')"></i>
                        <i class="fa-solid fa-upload" title="Upload"></i>
                        <i class="fa-solid fa-circle-info" title="Info" onclick="showInfo(repo)"></i>
                        <a href="https://github.com/${repo.repo}" target="_blank" title="Open Repo"><i class="fa-solid fa-globe"></i></a>
                    </div>`;
            }},
        ];
    },

    render: function(elementId, data) {
        try {
            if (typeof Tabulator === 'undefined') {
                throw new Error("Tabulator library is not loaded");
            }

            const container = document.querySelector(elementId);
            if (!container) throw new Error(`Element ${elementId} not found`);
            
            container.innerHTML = ''; // Clear existing content
            
            // Create Filter Bar
            const filterBar = document.createElement('div');
            filterBar.className = 'flex gap-4 p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700';
            filterBar.innerHTML = `
                <div class="flex items-center gap-2">
                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Search:</span>
                    <input type="text" id="git-search" class="px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 outline-none bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white" placeholder="Filter repos...">
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Exclude:</span>
                    <input type="text" id="git-exclude" class="px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-blue-500 outline-none bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white" placeholder="Exclude patterns...">
                </div>
            `;
            
            // Create Table Element
            const tableEl = document.createElement('div');
            tableEl.className = 'flex-1 h-full';
            
            container.appendChild(filterBar);
            container.appendChild(tableEl);
            
            const table = new Tabulator(tableEl, {
                data: data,
                layout: "fitColumns",
                height: "100%",
                groupBy: "user",
                groupHeader: function(value, count, data, group) {
                    return `<span style="color: #0969da; font-weight: 600; font-size: 16px;">${value} (${count} repos)</span>`;
                },
                columns: this.getColumns(),
            });

            // Filter Logic
            const applyFilters = () => {
                const searchVal = document.getElementById('git-search')?.value || '';
                const excludeVal = document.getElementById('git-exclude')?.value || '';
                
                table.setFilter(function(data) {
                    const repo = data.repo || '';
                    
                    // Exclude supersedes search: if it matches exclude, it's hidden immediately
                    if (excludeVal && repo.toLowerCase().includes(excludeVal.toLowerCase())) {
                        return false;
                    }
                    
                    // Then apply search filter
                    if (searchVal && !repo.toLowerCase().includes(searchVal.toLowerCase())) {
                        return false;
                    }
                    
                    return true;
                });
            };

            container.addEventListener('input', (e) => {
                if (e.target.id === 'git-search' || e.target.id === 'git-exclude') {
                    applyFilters();
                }
            });

            return table;
        } catch (e) {
            console.error("[GitTableConfig] Render error:", e);
            throw e;
        }
    }
};
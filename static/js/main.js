// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const requirementForm = document.getElementById('requirementForm');
    const searchInput = document.getElementById('searchInput');

    if (requirementForm) {
        requirementForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log("Form submitted");
            
            const requirement = document.getElementById('requirement').value;
            if (!requirement) return;

            try {
                console.log("Sending request to /api/v1/test-cases");
                const response = await fetch('/api/v1/test-cases', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ requirement })
                });

                const data = await response.json();
                console.log("Response received:", data);
                
                if (response.ok) {
                    displayTestCase(data.test_case);
                    document.getElementById('results').style.display = 'block';
                } else {
                    alert(`Error: ${data.message}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to generate test case');
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounce(async (e) => {
            const query = e.target.value;
            if (!query) {
                document.getElementById('searchResults').innerHTML = '';
                return;
            }

            try {
                const response = await fetch(`/api/v1/test-cases/search?q=${encodeURIComponent(query)}`);
                const data = await response.json();
                
                if (response.ok) {
                    displaySearchResults(data.results);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }, 500));
    }
});

function displayTestCase(testCase) {
    const html = `
        <div class="test-case">
            <h3>${testCase.name}</h3>
            <p><strong>Description:</strong> ${testCase.description}</p>
            <div class="steps">
                <h4>Steps:</h4>
                <ol>
                    ${testCase.steps.map(step => `<li>${step}</li>`).join('')}
                </ol>
            </div>
            <div class="expected-results">
                <h4>Expected Results:</h4>
                <ol>
                    ${testCase.expected_results.map(result => `<li>${result}</li>`).join('')}
                </ol>
            </div>
        </div>
    `;
    document.getElementById('testCaseResults').innerHTML = html;
}

function displaySearchResults(results) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<p>No results found</p>';
        return;
    }

    const html = results.map(result => `
        <div class="test-case">
            <h3>${result.name || 'Untitled'}</h3>
            <p class="score">Relevance Score: ${((result.relevance_score || 0) * 100).toFixed(1)}%</p>
            <p>${result.description || 'No description available'}</p>
            <div class="steps">
                <h4>Steps:</h4>
                <ul>
                    ${(result.steps || []).map(step => `<li>${step}</li>`).join('')}
                </ul>
                <h4>Expected Results:</h4>
                <ul>
                    ${(result.expected_results || []).map(result => `<li>${result}</li>`).join('')}
                </ul>
            </div>
            <p>Priority: ${result.priority || 'Medium'}</p>
            <p>Tags: ${(result.tags || []).join(', ') || 'No tags'}</p>
        </div>
    `).join('');
    
    resultsDiv.innerHTML = html;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Update the search function
async function searchTestCases() {
    const query = document.getElementById('searchQuery').value;
    const resultsDiv = document.getElementById('searchResults');
    
    try {
        console.log('Searching for:', query);
        const response = await fetch(`/api/v1/test-cases/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        console.log('Search results:', data);
        
        if (response.ok) {
            displaySearchResults(data.results);
        } else {
            resultsDiv.innerHTML = `<div class="error">Error: ${data.error || 'Search failed'}</div>`;
        }
    } catch (error) {
        console.error('Search error:', error);
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

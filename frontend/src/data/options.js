export const ROLES = [
  // Engineering
  { group: 'Engineering', value: 'software_engineer', label: 'Software Engineer' },
  { group: 'Engineering', value: 'frontend_developer', label: 'Frontend Developer' },
  { group: 'Engineering', value: 'backend_developer', label: 'Backend Developer' },
  { group: 'Engineering', value: 'fullstack_developer', label: 'Full Stack Developer' },
  { group: 'Engineering', value: 'devops_engineer', label: 'DevOps Engineer' },
  { group: 'Engineering', value: 'cloud_engineer', label: 'Cloud Engineer' },
  { group: 'Engineering', value: 'mobile_developer', label: 'Mobile Developer' },
  { group: 'Engineering', value: 'qa_engineer', label: 'QA Engineer' },
  { group: 'Engineering', value: 'embedded_engineer', label: 'Embedded Engineer' },

  // Data & AI
  { group: 'Data & AI', value: 'data_analyst', label: 'Data Analyst' },
  { group: 'Data & AI', value: 'data_scientist', label: 'Data Scientist' },
  { group: 'Data & AI', value: 'data_engineer', label: 'Data Engineer' },
  { group: 'Data & AI', value: 'ml_engineer', label: 'ML Engineer' },
  { group: 'Data & AI', value: 'ai_researcher', label: 'AI Researcher' },
  { group: 'Data & AI', value: 'business_analyst', label: 'Business Analyst' },

  // Security & GRC
  { group: 'Security & GRC', value: 'cybersecurity_analyst', label: 'Cybersecurity Analyst' },
  { group: 'Security & GRC', value: 'grc_analyst', label: 'GRC Analyst' },
  { group: 'Security & GRC', value: 'security_engineer', label: 'Security Engineer' },
  { group: 'Security & GRC', value: 'penetration_tester', label: 'Penetration Tester' },
  { group: 'Security & GRC', value: 'soc_analyst', label: 'SOC Analyst' },

  // Management
  { group: 'Management', value: 'product_manager', label: 'Product Manager' },
  { group: 'Management', value: 'project_manager', label: 'Project Manager' },
  { group: 'Management', value: 'scrum_master', label: 'Scrum Master' },
  { group: 'Management', value: 'it_manager', label: 'IT Manager' },

  // Finance & Consulting
  { group: 'Finance & Consulting', value: 'financial_analyst', label: 'Financial Analyst' },
  { group: 'Finance & Consulting', value: 'investment_analyst', label: 'Investment Analyst' },
  { group: 'Finance & Consulting', value: 'management_consultant', label: 'Management Consultant' },
  { group: 'Finance & Consulting', value: 'it_consultant', label: 'IT Consultant' },

  // Infrastructure
  { group: 'Infrastructure', value: 'network_engineer', label: 'Network Engineer' },
  { group: 'Infrastructure', value: 'database_administrator', label: 'Database Administrator' },
  { group: 'Infrastructure', value: 'system_administrator', label: 'System Administrator' },
  { group: 'Infrastructure', value: 'it_support', label: 'IT Support' },
]

export const EXPERIENCE_LEVELS = [
  { value: 'intern', label: 'Intern' },
  { value: 'junior', label: 'Junior (0-2 years)' },
  { value: 'mid', label: 'Mid (2-5 years)' },
  { value: 'senior', label: 'Senior (5+ years)' },
  { value: 'lead', label: 'Lead / Staff' },
  { value: 'manager', label: 'Manager' },
]

export const CODING_TOPICS = [
  { group: 'CS Fundamentals', value: 'arrays', label: 'Arrays' },
  { group: 'CS Fundamentals', value: 'strings', label: 'Strings' },
  { group: 'CS Fundamentals', value: 'linked lists', label: 'Linked Lists' },
  { group: 'CS Fundamentals', value: 'stacks and queues', label: 'Stacks & Queues' },
  { group: 'CS Fundamentals', value: 'hash tables', label: 'Hash Tables' },
  { group: 'CS Fundamentals', value: 'recursion', label: 'Recursion' },
  { group: 'Algorithms', value: 'sorting', label: 'Sorting' },
  { group: 'Algorithms', value: 'binary search', label: 'Binary Search' },
  { group: 'Algorithms', value: 'two pointers', label: 'Two Pointers' },
  { group: 'Algorithms', value: 'sliding window', label: 'Sliding Window' },
  { group: 'Algorithms', value: 'dynamic programming', label: 'Dynamic Programming' },
  { group: 'Algorithms', value: 'greedy algorithms', label: 'Greedy Algorithms' },
  { group: 'Algorithms', value: 'backtracking', label: 'Backtracking' },
  { group: 'Data Structures', value: 'trees', label: 'Trees' },
  { group: 'Data Structures', value: 'binary trees', label: 'Binary Trees' },
  { group: 'Data Structures', value: 'graphs', label: 'Graphs' },
  { group: 'Data Structures', value: 'heaps', label: 'Heaps' },
  { group: 'Data Structures', value: 'tries', label: 'Tries' },
  { group: 'Data & SQL', value: 'SQL queries', label: 'SQL Queries' },
  { group: 'Data & SQL', value: 'data cleaning', label: 'Data Cleaning' },
  { group: 'Data & SQL', value: 'pandas operations', label: 'Pandas Operations' },
  { group: 'Data & SQL', value: 'statistics problems', label: 'Statistics Problems' },
  { group: 'Security', value: 'cryptography basics', label: 'Cryptography Basics' },
  { group: 'Security', value: 'network security', label: 'Network Security' },
]

export const INTERVIEW_TYPES = [
  { value: 'behavioral', label: 'Behavioral', desc: 'Situation-based STAR questions' },
  { value: 'technical', label: 'Technical', desc: 'Concepts & problem solving' },
  { value: 'system_design', label: 'System Design', desc: 'Architecture & scalability' },
  { value: 'hr', label: 'HR Round', desc: 'Culture fit & motivation' },
  { value: 'case_study', label: 'Case Study', desc: 'Business & analytical cases' },
  { value: 'domain', label: 'Domain Specific', desc: 'Role-specific knowledge' },
]
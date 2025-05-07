// Simple script to test Supabase connection
const { createClient } = require('@supabase/supabase-js');

// Get Supabase URL from command line argument or prompt user
const SUPABASE_URL = process.argv[2] || process.env.SUPABASE_URL;
const SUPABASE_KEY = 'sbp_dda50b9feeee3b11f3b5fe0f178f03f94e8b8641';

if (!SUPABASE_URL) {
  console.error('Please provide your Supabase project URL as a command line argument:
  node supabase-test.js https://your-project-url.supabase.co');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

async function testConnection() {
  try {
    console.log('Attempting to connect to Supabase...');
    
    // Try to get the user (this will test authentication)
    const { data, error } = await supabase.auth.getUser();
    
    if (error) {
      console.error('Error connecting to Supabase:', error.message);
      return;
    }
    
    console.log('Successfully connected to Supabase!');
    console.log('User data:', data);
    
    // You can add more tests here, like listing tables or querying data
  } catch (err) {
    console.error('Unexpected error:', err.message);
  }
}

testConnection();

const axios = require('axios');
axios.get('http://localhost:8001/tools/registry').then(r => {
  console.log("Count:", r.data.length);
  const first = r.data[0];
  console.log("Sample:", first);
  // Check for any missing fields
  const missing = r.data.filter(t => !t.name || !t.type || !t.icon || !t.status || !t.description);
  console.log("Missing fields in:", missing);
}).catch(console.error);

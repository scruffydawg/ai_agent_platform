import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  page.on('response', response => {
    if(!response.ok()) console.log('PAGE RES ERR:', response.url(), response.status());
  });

  await page.goto('http://127.0.0.1:5173/');
  
  // Wait for React to render
  await new Promise(r => setTimeout(r, 2000));
  
  // click on Tool Registry
  await page.evaluate(() => {
    const navItems = Array.from(document.querySelectorAll('.nav-item'));
    const registryBtn = navItems.find(el => el.textContent.includes('Registry'));
    if (registryBtn) registryBtn.click();
  });
  
  await new Promise(r => setTimeout(r, 2000));
  console.log("Done");
  await browser.close();
})();

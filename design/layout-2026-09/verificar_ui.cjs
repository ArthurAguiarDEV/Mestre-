// QA visual do protótipo. Requer Playwright já instalado; nenhum pacote é baixado.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.BROWSER_CHANNEL ? {channel:process.env.BROWSER_CHANNEL} : {})});
  const checks = [], errors = [], requests = [];
  const base = pathToFileURL(path.join(__dirname,'app.html')).href;
  const context = await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  const page = await context.newPage();
  page.on('pageerror',error => errors.push(error.message));
  page.on('request',request => {if(/^https?:/.test(request.url())) requests.push(request.url());});
  async function noOverflow(label) {
    const sizes = await page.evaluate(() => ({page:document.documentElement.scrollWidth,view:innerWidth}));
    assert(sizes.page <= sizes.view + 1, `${label}: overflow ${JSON.stringify(sizes)}`);
    checks.push(`${label}: sem rolagem horizontal externa`);
  }
  for (const model of ['orbita','aurora','pulso']) {
    const theme = model==='aurora'?'light':'dark';
    for (const width of [1440,800,390]) {
      await page.setViewportSize({width,height:width===390?844:1000});
      await page.goto(`${base}?modelo=${model}&tema=${theme}`);
      await page.waitForSelector('main h1');
      if(model==='aurora')assert.equal(await page.locator('.aurora-home > .grid-two').first().locator(':scope > section').count(),2);
      await noOverflow(`${model} ${width}`);
      if(width!==800)await page.screenshot({path:path.join(__dirname,`${model}-${width===390?'mobile':'desktop'}.png`),fullPage:true});
      if(width===390){
        const menu = page.locator('[data-menu]');
        if(await menu.count())await menu.click();
        await page.locator('.nav-item[data-page="evolve"]').click();
        await noOverflow(`${model} teste mobile`);
        await page.screenshot({path:path.join(__dirname,`${model}-validacao-mobile.png`),fullPage:true});
        for(const destination of ['chat','voice','media','flow','memory','settings']){
          const toggle=page.locator('[data-menu]');
          if(await toggle.count())await toggle.click();
          await page.locator(`.nav-item[data-page="${destination}"]`).click();
          await noOverflow(`${model} ${destination} mobile`);
        }
      }
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.goto(`${base}?modelo=${model}&tema=${theme==='dark'?'light':'dark'}`);
    await page.screenshot({path:path.join(__dirname,`${model}-tema-alternativo.png`),fullPage:true});
    await page.goto(`${base}?modelo=${model}&tema=${theme}`);
    await page.locator('button[data-theme]').click();
    assert.equal(await page.locator('body').getAttribute('data-theme'),theme==='dark'?'light':'dark');
    checks.push(`${model}: troca de tema`);
    await page.locator('.toolbar [data-search], .aurora-top [data-search]').click();
    await page.locator('#search-input').fill('Spotify');
    assert.equal(await page.locator('#search-results button').count(),1);
    await page.locator('#search-results button').click();
    await page.locator('[data-tab="Serviços"]').click();
    assert.equal(await page.locator('.service-card').count(),6);
    checks.push(`${model}: busca, navegação e serviços`);
    await page.locator('.nav-item[data-page="voice"]').click();
    const toggle = page.locator('[role="switch"]').first();
    const before = await toggle.getAttribute('aria-checked');
    await toggle.click();
    assert.notEqual(await toggle.getAttribute('aria-checked'),before);
    await page.locator('.nav-item[data-page="chat"]').click();
    await page.locator('#chat-form input').fill('Mensagem de avaliação visual');
    await page.locator('#chat-form button').click();
    assert(await page.getByText('Mensagem de avaliação visual',{exact:true}).isVisible());
    checks.push(`${model}: controles e conversa demonstrativa`);
    await page.locator('.nav-item[data-page="evolve"]').click();
    const first = await page.locator('.say').textContent();
    for(const result of ['pass','fail','skip','pass'])await page.locator(`[data-result="${result}"]`).click();
    assert(await page.getByText('Seu retorno está organizado.',{exact:true}).isVisible());
    const downloadPromise=page.waitForEvent('download');
    await page.locator('[data-export-tests]').click();
    assert((await downloadPromise).suggestedFilename().startsWith('DEMONSTRACAO-'));
    await page.locator('[data-new-round]').first().click();
    assert(await page.locator('.say').isVisible());
    checks.push(`${model}: quatro respostas, resumo, exportação e nova rodada`);
    await page.locator('.toolbar [data-feedback], .aurora-top [data-feedback]').click();
    await page.locator('[name="liked"]').fill('Navegação clara');
    await page.locator('[name="change"]').fill('Avaliar contraste no uso real');
    const pref=page.waitForEvent('download');
    await page.locator('#feedback-form [type="submit"]').click();
    assert.equal((await pref).suggestedFilename(),'preferencia-layout-mestre.md');
    checks.push(`${model}: preferência baixável, sem transmissão`);
  }
  await page.goto(pathToFileURL(path.join(__dirname,'index.html')).href);
  await page.setViewportSize({width:1440,height:1100});
  await page.screenshot({path:path.join(__dirname,'galeria-desktop.png'),fullPage:true});
  assert.equal(await page.locator('.proposal').count(),3);
  const images=await page.locator('img').evaluateAll(images=>images.every(i=>i.complete&&i.naturalWidth>0));
  assert(images,'Previews da galeria precisam carregar');
  await page.setViewportSize({width:390,height:844});
  await noOverflow('galeria mobile');
  assert.deepEqual(errors,[],'Erros de JavaScript');
  assert.deepEqual(requests,[],'O protótipo deve funcionar sem requests HTTP externos');
  const result={checkedAt:new Date().toISOString(),status:'PASS',checks,errors,externalRequests:requests,
    limits:['Não testa o Mestre real, áudio ou monitores físicos.','Sem auditoria completa de acessibilidade.']};
  fs.writeFileSync(path.join(__dirname,'verificacao-ui.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});

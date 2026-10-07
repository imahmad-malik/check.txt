#!/usr/bin/env python3
"""Real HTTP schema/canonical tests; provider signals are clearly SIMULATED.

The temporary local-only MU plugin is never included in an installable ZIP.
Official SEO plugin downloads were denied (403); this does not establish actual
Yoast/Rank Math/AIOSEO/SEOPress distribution compatibility.
"""
import json,re,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
SITE='http://127.0.0.1:8766'
MU=Path('/workspace/wp-test/wordpress/wp-content/mu-plugins/isolated-qa-seo-signals.php')
SOURCE='''<?php
if (!defined('ABSPATH') || wp_get_environment_type() !== 'local' || (int)get_option('blog_public') !== 0) { return; }
$provider=$_GET['isolated_qa_provider']??'';
$signals=['yoast'=>'WPSEO_VERSION','rankmath'=>'RANK_MATH_VERSION','aioseo'=>'AIOSEO_VERSION','seopress'=>'SEOPRESS_VERSION'];
if(isset($signals[$provider])) { define($signals[$provider], 'ISOLATED-SIMULATION'); }
elseif($provider==='filter') { add_filter('bixie_external_schema_provider','__return_true'); }
else { return; }
add_action('wp_head',static function(){ echo '<script type="application/ld+json" class="isolated-qa-provider-data">{"@context":"https://schema.org","@type":"WebPage","name":"ISOLATED SIMULATED PROVIDER"}</script>'; },31);
'''

def fetch(path):
    with urllib.request.urlopen(SITE+path,timeout=20) as response:
        html=response.read().decode();headers=dict(response.headers)
    own=re.findall(r'<script type="application/ld\+json" class="bixie-structured-data">(.*?)</script>',html,re.S)
    canonical=re.findall(r'<link rel="canonical" href="(.*?)"',html)
    robots=re.findall(r'<meta name=[\'"]robots[\'"] content=[\'"](.*?)[\'"]',html)
    titles=re.findall(r'<h3><a[^>]+>(.*?)</a></h3>',html)
    return {'html':html,'headers':headers,'schema':[json.loads(item) for item in own],'canonical':canonical,'robots':robots,'titles':titles}

def main():
    report={'purpose':'Actual WordPress HTTP checks with synthetic CODE records. External provider detection signals are SIMULATED; no third-party plugin distribution was installed.','officialPluginDistributionAccess':{'metadata':403,'download':403,'actualThirdPartyPluginActivation':'not verified'},'checks':{}}
    if MU.exists():raise RuntimeError('A temporary provider fixture already exists; preserve it for inspection.')
    MU.parent.mkdir(exist_ok=True);MU.write_text(SOURCE)
    try:
        base=fetch('/isolated-code-test-library/');assert len(base['schema'])==1 and base['canonical']==[SITE+'/isolated-code-test-library/']
        gallery=next(item for item in base['schema'][0]['@graph'] if item['@type']=='ImageGallery');assert [item['name'] for item in gallery['hasPart']]==base['titles']
        assert len(gallery['hasPart'])==6 and all(len(item['image'])==3 for item in gallery['hasPart'])
        assert all(image['width']==7680 and image['height']==512 for item in gallery['hasPart'] for image in item['image'])
        assert 'AggregateRating' not in json.dumps(base['schema']) and 'ratingValue' not in json.dumps(base['schema'])
        report['checks']['schemaMatchesSixServerCardsAndThreeActualAngles']=True
        page2=fetch('/isolated-code-test-library/?bixie_page=2');gallery2=next(item for item in page2['schema'][0]['@graph'] if item['@type']=='ImageGallery')
        assert page2['canonical']==[SITE+'/isolated-code-test-library/?bixie_page=2'] and [item['name'] for item in gallery2['hasPart']]==page2['titles'];report['checks']['paginationCanonicalAndSchemaAligned']=True
        filtered=fetch('/isolated-code-test-library/?texture=wavy');assert not filtered['schema'] and filtered['canonical']==[SITE+'/isolated-code-test-library/']
        assert 'noindex' in ','.join(filtered['robots']) and 'nofollow' in ','.join(filtered['robots']) and 'follow' not in [s.strip() for s in ','.join(filtered['robots']).split(',')]
        assert filtered['headers'].get('X-Robots-Tag')=='noindex, nofollow';report['checks']['facetsNoindexAndOwnerPrivacyPreserved']=True
        providers={}
        for provider in ['yoast','rankmath','aioseo','seopress','filter']:
            response=fetch('/isolated-code-test-library/?isolated_qa_provider='+provider)
            assert not response['schema'] and response['html'].count('class="isolated-qa-provider-data"')==1
            providers[provider]={'simulatedSignal':True,'bixieSchemaSuppressed':True,'providerOwnedMarkerRetained':True}
        report['simulatedProviders']=providers
        # Exercise the actual owner setting, then restore its original value.
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(storage_state='/workspace/wp-test/qa-auth-state.json');page=context.new_page()
            page.goto(SITE+'/wp-admin/tools.php?page=bixie-setup',wait_until='networkidle');control=page.locator('input[name="disabled"]');original=control.is_checked()
            try:
                control.check();page.locator('form').filter(has=control).locator('input[type="submit"]').click();page.wait_for_load_state('networkidle');assert not fetch('/isolated-code-test-library/')['schema'];report['checks']['actualAdminSchemaDisableSetting']=True
            finally:
                page.goto(SITE+'/wp-admin/tools.php?page=bixie-setup',wait_until='networkidle');page.locator('input[name="disabled"]').set_checked(original);page.locator('form').filter(has=page.locator('input[name="disabled"]')).locator('input[type="submit"]').click();page.wait_for_load_state('networkidle');context.close();browser.close()
    finally:MU.unlink(missing_ok=True)
    report['status']='passed';report['temporaryProviderFixtureRemoved']=True;report['ownerSchemaSettingRestored']=True
    (ROOT/'wp-seo-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()

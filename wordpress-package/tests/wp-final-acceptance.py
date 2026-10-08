#!/usr/bin/env python3
"""Assemble final actual-source acceptance only after all required live checks pass."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from wp_final_common import inspect, TESTS


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True);parser.add_argument('--parts',type=Path,required=True);args=parser.parse_args()
    destination=TESTS/'wp-final-acceptance-report.json'
    report={'generatedAtUTC':datetime.now(timezone.utc).isoformat(),'scope':'Actual complete final media uploaded through native owner GUI and imported into the separate WordPress local noindex site; final delivered theme and plugin ZIPs installed through WordPress core. Synthetic fixtures and pilot-only reports are excluded.','passed':False,'actual_counts':{},'tested_archives':{},'checks':{},'limits':{'actualWordPressRemoteHTTPSFetch':'Unverified in this cloud runtime: WordPress safe URL validation requires GitHub DNS before the configured HTTPS proxy; URL/DNS/TLS checks remain enabled. Actual owner GUI local multipart upload is verified.','namedSEOPlugin':'Actual Yoast/Rank Math/AIOSEO/SEOPress distributions unavailable from official endpoints (403); provider signals were explicitly simulated in earlier isolated checks.','productionHosting':'No production hosting, search indexing, guaranteed rankings, or field Core Web Vitals claim.','motionSource':'The real MP4 is a silent photographic sequence made from distinct corresponding reviewed front/side/back original photographs; it is not live-action salon footage.'}}
    def save():destination.write_text(json.dumps(report,indent=2)+'\n')
    try:
        reports={}
        for name in ['wp-final-core-zip-report.json','wp-final-final-import-report.json','wp-final-final-browser-report.json','wp-final-home-report.json','wp-final-final-editability-report.json','wp-final-permalink-report.json']:
            data=json.loads((TESTS/name).read_text());assert data.get('passed') is True,name;reports[name]=data
        state=inspect(); counts=state['databaseCounts'];home=state['home']
        report['actual_counts']={**counts,'home_unique_image_elements':len(home['uniquePhotoIDs']),'home_distinct_video_posters':len(set(home['posterIDs'])),'home_unique_photos_including_poster':len(home['visiblePhotoIDs']),'home_sections':home['sectionCount'],'guide_photo_references':sum(len(guide['nativePhotoIDs']) for guide in state['guides'].values())};save()
        for key,expected in [('looks',154),('publishedLooks',154),('photos',487),('films',1),('uniqueSourceSHA256',488),('pages',42),('collections',22),('readyCollections',22),('guides',7),('readyGuides',7)]:assert counts[key]==expected,(key,counts[key])
        assert not state['duplicateImportKeys']
        assert report['actual_counts']['guide_photo_references']==24
        assert home['status']=='publish' and home['gate']['complete'] and len(home['uniquePhotoIDs'])==77 and len(home['visiblePhotoIDs'])==78 and home['sectionCount']==22
        assert state['settings']['show_on_front']=='page' and int(state['settings']['page_on_front'])==home['id']
        assert state['pages']['privacy']['status']=='draft' and state['pages']['contact']['status']=='draft'
        assert all(look['status']=='publish' and look['gate']['complete'] and {image['angle'] for image in look['images']}=={'front','side','back'} for look in state['looks'].values())
        assert all(collection['gate']['complete'] and collection['gate']['photos']==21 and collection['gate']['looks']==7 for collection in state['collections'].values())
        assert all(guide['status']=='publish' and guide['gate']['complete'] for guide in state['guides'].values())
        assert all(attachment['sourceExists'] and attachment['displayExists'] and attachment['approved'] and attachment['qualified'] and attachment['sourceSHA256']==attachment['expectedSHA256'] for attachment in state['attachments'].values())
        for kind,filename in [('theme','bixie-editorial.zip'),('plugin','bixie-library.zip')]:
            path=args.release/filename;digest=hashlib.sha256(path.read_bytes()).hexdigest();assert reports['wp-final-core-zip-report.json']['archives'][kind]['sha256']==digest;report['tested_archives'][filename]=digest
        index=json.loads((args.parts/'media-download-manifest.json').read_text())
        for part in index['parts']:
            name=Path(part.get('filename') or part['file']).name;path=args.parts/name;digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==part['sha256'] and path.stat().st_size==part['bytes'] and path.stat().st_size<=25*1024*1024
            actual=next((item for item in reports['wp-final-final-import-report.json']['parts'] if item['filename']==name),None);assert actual and actual['sha256']==digest and state['parts'][actual['bundleID']]['archive_sha256']==digest;report['tested_archives'][name]=digest
        report['checks']={'completeActual154Look487PhotoInventoryAndOneQualifiedPhotographicFilm':True,'all22CollectionsHaveSevenCoherentLooksAnd21DistinctActualViews':True,'all42NativePagesAndSevenPublishedGuidesWith24PhotoReferences':True,'publicHome77UniqueImageElementsOneDistinctPoster22Sections':True,'actualNativeGutenbergRoundtripAndOwnerGUISavePreservation':True,'actualFinalDeliveredCoreZIPsAndAllMultipartSHA256Verified':True,'publicHTTPNaturalAspectSelectedPaintedEdgesNoJavaScriptGETAndPlainPrettyPermalinks':True,'actualDecodedFilmMotionAutoplayNativeKeyboardReducedMotionAndPhotoFlow':True}
        report['supporting_reports']=list(reports);report['passed']=True
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        save();print(json.dumps({'passed':report['passed'],'report':str(destination),'actual_counts':report['actual_counts'],'tested_archive_count':len(report['tested_archives']),'failure':report.get('failure')},indent=2))


if __name__=='__main__':main()

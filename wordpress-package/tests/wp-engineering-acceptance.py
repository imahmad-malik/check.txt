#!/usr/bin/env python3
"""Scoped engineering checkpoint proof; never approves the missing full library."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from wp_final_common import inspect, TESTS


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True);parser.add_argument('--parts',type=Path,required=True);args=parser.parse_args()
    report={'generatedAtUTC':datetime.now(timezone.utc).isoformat(),'release_scope':'engineering_installable_media_incomplete','scope':'Actual current complete-look checkpoint installed through WordPress core ZIPs and actual source multipart owner GUI uploads on a separate local noindex site. The 154-look/487-photo target is incomplete; no full-library acceptance or public Home claim.','passed':False,'full_library_complete':False,'actual_counts':{},'tested_archives':{},'checks':{},'remaining_target':{'looks':26,'photos':65,'ready_collections':6},'limits':{'generation':'Image provider confirmed daily-quota HTTP429; 65 required source photographs remain unavailable until quota reset.','actualWordPressRemoteHTTPSFetch':'Unverified cloud limitation: WordPress safe URL validation requires GitHub DNS before the configured proxy. URL/DNS/TLS checks remain enabled; actual authenticated owner GUI manual multipart uploads are verified.','namedSEOPlugin':'Actual named SEO distributions were unavailable from official endpoints (403); previous provider signals were explicitly simulated.','productionHosting':'No production hosting, indexing, guaranteed ranking, or field Core Web Vitals claim.','film':'Silent photographic sequence from distinct corresponding reviewed front/side/back original photographs, not live-action salon footage.'}}
    destinations=[TESTS/'wp-engineering-acceptance-report.json',TESTS/'wp-saved-acceptance-report.json']
    def save():
        for destination in destinations:destination.write_text(json.dumps(report,indent=2)+'\n')
    try:
        names=['wp-engineering-core-zip-report.json','wp-final-engineering-import-report.json','wp-final-engineering-browser-report.json','wp-final-engineering-editability-report.json','wp-engineering-home-report.json','wp-final-directory-regression-report.json','wp-final-alias-report.json','wp-final-permalink-report.json']
        supporting={}
        for name in names:
            data=json.loads((TESTS/name).read_text());assert data.get('passed') is True,name;supporting[name]=data
        state=inspect();counts=state['databaseCounts'];home=state['home']
        report['actual_counts']={**counts,'home_unique_image_elements':len(home['uniquePhotoIDs']),'home_distinct_video_posters':len(set(home['posterIDs'])),'home_unique_photos_including_poster':len(home['visiblePhotoIDs']),'home_sections':home['sectionCount'],'home_status':home['status'],'home_full_library_gate_complete':home['gate']['complete'],'guide_photo_references':sum(len(guide['nativePhotoIDs']) for guide in state['guides'].values())};save()
        for key,expected in [('looks',128),('publishedLooks',128),('photos',422),('films',1),('uniqueSourceSHA256',423),('pages',42),('collections',22),('readyCollections',16),('guides',7),('readyGuides',7)]:assert counts[key]==expected,(key,counts[key])
        assert not state['duplicateImportKeys'] and report['actual_counts']['guide_photo_references']==24
        assert home['status']=='draft' and not home['gate']['complete'] and state['settings']['show_on_front']!='page'
        assert state['pages']['privacy']['status']=='draft' and state['pages']['contact']['status']=='draft'
        assert all(look['status']=='publish' and look['gate']['complete'] and {image['angle'] for image in look['images']}=={'front','side','back'} for look in state['looks'].values())
        assert all(collection['gate']['photos']==21 and collection['gate']['looks']==7 for collection in state['collections'].values() if collection['gate']['complete'])
        assert all(guide['status']=='publish' and guide['gate']['complete'] for guide in state['guides'].values())
        assert all(attachment['sourceExists'] and attachment['displayExists'] and attachment['approved'] and attachment['qualified'] and attachment['sourceSHA256']==attachment['expectedSHA256'] for attachment in state['attachments'].values())
        for kind,filename in [('theme','bixie-editorial.zip'),('plugin','bixie-library.zip')]:
            path=args.release/filename;digest=hashlib.sha256(path.read_bytes()).hexdigest();assert supporting['wp-engineering-core-zip-report.json']['archives'][kind]['sha256']==digest;report['tested_archives'][filename]=digest
        index=json.loads((args.parts/'media-download-manifest.json').read_text())
        for part in index['parts']:
            name=Path(part.get('filename') or part['file']).name;path=args.parts/name;digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==part['sha256'] and path.stat().st_size==part['bytes'] and path.stat().st_size<=25*1024*1024
            actual=next((item for item in supporting['wp-final-engineering-import-report.json']['parts'] if item['filename']==name),None);assert actual and actual['sha256']==digest and state['parts'][actual['bundleID']]['archive_sha256']==digest;report['tested_archives'][name]=digest
        assert len(supporting['wp-final-engineering-import-report.json']['parts'])==len(index['parts'])
        assert supporting['wp-final-engineering-import-report.json']['expectedSuppliedUniqueMedia']==423
        report['checks']={'actual128CoherentPublishedLooksAnd422ReviewedNativePhotoSourcesOneQualifiedFilm':True,'all16ReadyCollectionsHaveSevenLooksAnd21DistinctActualViews':True,'all42EditableNativePagesSevenReadyGuides24RealPhotoReferences':True,'unfinishedHomeRemainsDraftWithPublicationGatesEnabled':True,'actualCoreZIPInstallAndAll423MediaManualOwnerGUIUploadImportSHAs':True,'actualRepeatedPreserveImportAndNativeOwnerGUISaveExactRestore':True,'actualCurrentPublicHTTPSourceHashesGeometryDetailNoJavaScriptGETAndNativeBlockRoundtrip':True,'actualFirstPassDirectoryPublicationAndOwnerEditedDraftPrivatePreservation':True,'actualAliasFiltersAndPlainPrettyPermalinks':True,'actualDraftHomeWholePhotosNineIndependentMovingNativeShelvesOpeningRailFilmReducedMotionPrintAndOwnerEditor':True}
        report['supporting_reports']=names;report['passed']=True
    except Exception as error:report['failure']=str(error);raise
    finally:
        save();print(json.dumps({'passed':report['passed'],'release_scope':report['release_scope'],'reports':[str(p) for p in destinations],'actual_counts':report['actual_counts'],'tested_archive_count':len(report['tested_archives']),'failure':report.get('failure')},indent=2))


if __name__=='__main__':main()

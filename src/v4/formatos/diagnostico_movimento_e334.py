"""E334: bounded camera registration on exact reviewed samples.
Feature matches outside declared evidence regions are technical hints only.
No identity, action, causality, or semantic coverage is inferred.
"""
import math

def _boxes(framing,i):
    if not framing:return []
    points=framing.get('pontos') or []
    if len(points)!=3:return []
    boxes=[]
    for e in points[i].get('elementos',[]):
        b=e.get('bbox')
        if isinstance(b,list) and len(b)==4 and all(type(x) in (int,float) and math.isfinite(x) for x in b) and 0<=b[0]<b[2]<=1 and 0<=b[1]<b[3]<=1:
            boxes.append(b)
    return boxes

def par(a,b,boxes_a=(),boxes_b=()):
    import cv2,numpy as np
    # No registration claimed if no declared region separates foreground.
    result={'status':'REFERENCIA_INSUFICIENTE','prova_semantica':False}
    if not boxes_a or not boxes_b:return result
    def prepare(im,boxes):
        w,h=im.size;scale=min(1,480/max(w,h));w,h=max(1,round(w*scale)),max(1,round(h*scale))
        gray=cv2.resize(np.asarray(im.convert('L')),(w,h),interpolation=cv2.INTER_AREA)
        mask=np.full((h,w),255,np.uint8)
        for x0,y0,x1,y1 in boxes:
            mask[max(0,int(y0*h)-4):min(h,math.ceil(y1*h)+4),max(0,int(x0*w)-4):min(w,math.ceil(x1*w)+4)]=0
        return gray,mask
    x,m=prepare(a,boxes_a);y,n=prepare(b,boxes_b)
    if x.shape!=y.shape:return result
    h,w=x.shape
    orb=cv2.ORB_create(nfeatures=900)
    ka,da=orb.detectAndCompute(x,m);kb,db=orb.detectAndCompute(y,n)
    if da is None or db is None or len(da)<12 or len(db)<12:return result
    matches=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(da,db,k=2)
    good=[v[0] for v in matches if len(v)==2 and v[0].distance<.75*v[1].distance]
    # Distinct target points; avoid a repeated texture dominating the fit.
    good=list({g.trainIdx:g for g in sorted(good,key=lambda g:-g.distance)}.values())
    if len(good)<12:return {**result,'matches':len(good)}
    p=np.float32([ka[g.queryIdx].pt for g in good]);q=np.float32([kb[g.trainIdx].pt for g in good])
    try:M,ok=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=2.5)
    except cv2.error:return result
    if M is None or ok is None:return result
    keep=ok.ravel().astype(bool);count=int(keep.sum())
    if count<10 or count/len(good)<.55:return {**result,'matches':len(good),'inliers':count}
    spread=np.ptp(p[keep],axis=0)
    if spread[0]<.2*w or spread[1]<.2*h:return {**result,'matches':len(good),'inliers':count}
    # Compare registered pixels only where both images actually overlap.
    warp=cv2.warpAffine(x,M,(w,h));valid=cv2.warpAffine(np.full_like(x,255),M,(w,h),flags=cv2.INTER_NEAREST)>0
    background=(cv2.warpAffine(m,M,(w,h),flags=cv2.INTER_NEAREST)>0)&(n>0)&valid
    foreground=(n==0)&valid
    if background.sum()<.08*w*h or foreground.sum()<.01*w*h:return result
    diff=np.abs(warp.astype(np.int16)-y.astype(np.int16))
    pts=p[keep];flow=pts@M[:,:2].T+M[:,2]-pts
    return {'status':'REGISTRO_TECNICO_ESTIMADO','matches':len(good),'inliers':count,
            'camera_deslocamento_relativo':round(float(np.linalg.norm(flow,axis=1).mean()/max(w,h)),5),
            'diferenca_fundo':round(float(diff[background].mean()),3),
            'diferenca_regiao':round(float(diff[foreground].mean()),3),
            'prova_semantica':False}

def diagnosticar(frames,times,framing):
    pairs=[]
    for i,j in ((0,1),(1,2),(0,2)):
        try:r=par(frames[i],frames[j],_boxes(framing,i),_boxes(framing,j))
        except Exception as exc:r={'status':'DIAGNOSTICO_INDISPONIVEL','reason':type(exc).__name__,'prova_semantica':False}
        pairs.append({'indices':[i,j],'tempos_s':[times[i],times[j]],**r})
    return {'pares':pairs,'prova_semantica':False,'prova_continua':False,'publicar':False}

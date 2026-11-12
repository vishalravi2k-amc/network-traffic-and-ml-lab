"""Reproduce three dataset-specific ML comparisons; no network access required.
Run from repository root: python ml/train_compare.py
"""
from pathlib import Path
import hashlib,json,platform
import numpy as np
import pandas as pd
import sklearn,joblib
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split,KFold,StratifiedGroupKFold,GridSearchCV
from sklearn.ensemble import AdaBoostRegressor,GradientBoostingRegressor,HistGradientBoostingRegressor,RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.cluster import KMeans,AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,confusion_matrix,silhouette_score,davies_bouldin_score,calinski_harabasz_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data';OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
SEED=42
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})

def prep(numeric,categorical):
 return ColumnTransformer([('number',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric),('category',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical)],sparse_threshold=0)

def run():
 report={'seed':SEED,'environment':{'python':platform.python_version(),'scikit_learn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__},'datasets':{},'regression':[],'classification':[],'clustering':[]}
 for f in DATA.glob('*.csv'):
  d=pd.read_csv(f);report['datasets'][f.name]={'rows':len(d),'columns':list(d.columns),'missing':int(d.isna().sum().sum()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 # Insurance: exact duplicate records are removed before the random split.
 raw=pd.read_csv(DATA/'insurance_pre.csv');d=raw.drop_duplicates();report['insurance_duplicate_rows_removed']=len(raw)-len(d)
 X=d.drop(columns='charges');y=d.charges
 Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=SEED)
 assert set(Xtr.index).isdisjoint(Xte.index)
 fold=KFold(n_splits=5,shuffle=True,random_state=SEED)
 candidates=[('AdaBoost',AdaBoostRegressor(random_state=SEED),{'model__n_estimators':[100,200],'model__learning_rate':[.05,.2]}),('Gradient Boosting',GradientBoostingRegressor(random_state=SEED),{'model__n_estimators':[100,200],'model__max_depth':[2,3],'model__learning_rate':[.05]}),('Histogram Gradient Boosting',HistGradientBoostingRegressor(random_state=SEED),{'model__max_iter':[100,200],'model__max_leaf_nodes':[7,15],'model__learning_rate':[.05]})]
 reg_models={};reg_pred=pd.DataFrame({'source_csv_line':Xte.index+2,'actual':yte.to_numpy()})
 for name,model,grid in candidates:
  pipe=Pipeline([('preprocess',prep(['age','bmi','children'],['sex','smoker'])),('model',model)])
  search=GridSearchCV(pipe,grid,scoring='neg_root_mean_squared_error',cv=fold,n_jobs=1,return_train_score=False).fit(Xtr,ytr)
  pred=search.predict(Xte);reg_models[name]=search.best_estimator_;reg_pred[name]=pred
  report['regression'].append({'algorithm':name,'cv_rmse':-search.best_score_,'cv_std':float(search.cv_results_['std_test_score'][search.best_index_]),'test_rmse':float(np.sqrt(mean_squared_error(yte,pred))),'test_mae':float(mean_absolute_error(yte,pred)),'test_r2':float(r2_score(yte,pred)),'parameters':search.best_params_})
  print('Regression:',name,report['regression'][-1]['test_rmse'],flush=True)
 reg_best=min(report['regression'],key=lambda r:r['cv_rmse']);report['regression_selected']=reg_best['algorithm'];report['regression_split']={'train':len(Xtr),'test':len(Xte),'cv_folds':5}
 joblib.dump(reg_models[reg_best['algorithm']],OUT/'insurance_selected_model.joblib');reg_pred.to_csv(OUT/'regression_predictions.csv',index=False)
 pd.DataFrame({'source_csv_line':d.index+2,'split':['train' if i in Xtr.index else 'test' for i in d.index]}).to_csv(OUT/'insurance_split.csv',index=False)
 fig,ax=plt.subplots(figsize=(7,4.4));ax.scatter(yte,reg_pred[reg_best['algorithm']],s=17,c='#247e6b',alpha=.65);lo=min(yte.min(),reg_pred[reg_best['algorithm']].min());hi=max(yte.max(),reg_pred[reg_best['algorithm']].max());ax.plot([lo,hi],[lo,hi],'--',c='#9aa8b2',lw=1);ax.set(xlabel='Actual charges (dataset units)',ylabel='Predicted charges (dataset units)',title=f'Insurance held-out predictions\n{reg_best["algorithm"]}');fig.tight_layout();fig.savefig(OUT/'insurance_predictions.png');plt.close(fig)
 # Ads: keep all distinct user records, but group identical model features.
 # The same Gender/Age/Salary combination cannot appear in train and test or opposite CV folds.
 d=pd.read_csv(DATA/'Social_Network_Ads.csv');X=d[['Gender','Age','EstimatedSalary']];y=d.Purchased
 groups=pd.factorize(pd.MultiIndex.from_frame(X))[0]
 outer=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=SEED)
 tr,te=next(outer.split(X,y,groups));Xtr,Xte,ytr,yte=X.iloc[tr],X.iloc[te],y.iloc[tr],y.iloc[te]
 assert set(groups[tr]).isdisjoint(groups[te]);inner=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=SEED)
 candidates=[('Logistic Regression',LogisticRegression(max_iter=2000,random_state=SEED),{'model__C':[.1,1,10]}),('RBF SVM',SVC(kernel='rbf',random_state=SEED),{'model__C':[.1,1,10],'model__gamma':['scale',.1]}),('K Nearest Neighbors',KNeighborsClassifier(),{'model__n_neighbors':[3,5,7,11]}),('Random Forest',RandomForestClassifier(n_estimators=200,random_state=SEED,n_jobs=1),{'model__max_depth':[3,5,None],'model__min_samples_leaf':[1,3]}),('Decision Tree',DecisionTreeClassifier(random_state=SEED),{'model__max_depth':[2,3,5,None],'model__min_samples_leaf':[3]}),('Gaussian Naive Bayes',GaussianNB(),{'model__var_smoothing':[1e-9,1e-7]})]
 cls_models={};cls_pred=pd.DataFrame({'source_csv_line':Xte.index+2,'actual':yte.to_numpy()})
 for name,model,grid in candidates:
  pipe=Pipeline([('preprocess',prep(['Age','EstimatedSalary'],['Gender'])),('model',model)])
  search=GridSearchCV(pipe,grid,scoring='accuracy',cv=inner,n_jobs=1).fit(Xtr,ytr,groups=groups[tr]);pred=search.predict(Xte)
  scores=search.decision_function(Xte) if hasattr(search,'decision_function') else search.predict_proba(Xte)[:,1]
  cls_models[name]=search.best_estimator_;cls_pred[name]=pred
  report['classification'].append({'algorithm':name,'cv_accuracy':search.best_score_,'cv_std':float(search.cv_results_['std_test_score'][search.best_index_]),'test_accuracy':float(accuracy_score(yte,pred)),'test_precision':float(precision_score(yte,pred,zero_division=0)),'test_recall':float(recall_score(yte,pred,zero_division=0)),'test_f1':float(f1_score(yte,pred,zero_division=0)),'test_roc_auc':float(roc_auc_score(yte,scores)),'confusion_matrix':confusion_matrix(yte,pred,labels=[0,1]).tolist(),'parameters':search.best_params_})
  print('Classification:',name,report['classification'][-1]['test_accuracy'],flush=True)
 cls_best=max(report['classification'],key=lambda r:r['cv_accuracy']);report['classification_selected']=cls_best['algorithm'];report['classification_split']={'train':len(Xtr),'test':len(Xte),'cv_folds':5,'feature_groups':len(set(groups)),'train_class_counts':ytr.value_counts().to_dict(),'test_class_counts':yte.value_counts().to_dict(),'grouping':'Gender, Age, EstimatedSalary'}
 joblib.dump(cls_models[cls_best['algorithm']],OUT/'ads_selected_model.joblib');cls_pred.to_csv(OUT/'classification_predictions.csv',index=False)
 pd.DataFrame({'source_csv_line':d.index+2,'group':groups,'split':['train' if i in tr else 'test' for i in d.index]}).to_csv(OUT/'ads_split.csv',index=False)
 cm=np.array(cls_best['confusion_matrix']);fig,ax=plt.subplots(figsize=(5.6,4.4));ax.imshow(cm,cmap='Greens');ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Not purchased','Purchased'],yticklabels=['Not purchased','Purchased'],xlabel='Predicted label',ylabel='Actual label',title=f'Held-out confusion matrix\n{cls_best["algorithm"]}')
 for i in range(2):
  for j in range(2):ax.text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=20,color='white' if cm[i,j]>cm.max()/2 else '#163e30')
 fig.tight_layout();fig.savefig(OUT/'ads_confusion_matrix.png');plt.close(fig)
 # Clustering: no target labels or holdout accuracy. Compare all algorithms on the SAME scaled 2D space.
 d=pd.read_csv(DATA/'Mall_Customers.csv');features=['Annual Income (k$)','Spending Score (1-100)'];scaler=StandardScaler();Z=scaler.fit_transform(d[features]);all_cluster=[];best_models={};assignments={}
 for name in ['K Means','Agglomerative Ward','Gaussian Mixture']:
  trials=[]
  for k in range(2,9):
   model=KMeans(n_clusters=k,n_init=20,random_state=SEED) if name=='K Means' else AgglomerativeClustering(n_clusters=k,linkage='ward') if name=='Agglomerative Ward' else GaussianMixture(n_components=k,n_init=5,random_state=SEED)
   labels=model.fit_predict(Z);score=float(silhouette_score(Z,labels));row={'algorithm':name,'clusters':k,'silhouette':score,'davies_bouldin':float(davies_bouldin_score(Z,labels)),'calinski_harabasz':float(calinski_harabasz_score(Z,labels))};trials.append(row);all_cluster.append(row)
   if name not in best_models or score>best_models[name][0]:best_models[name]=(score,model,labels)
  report['clustering'].append(max(trials,key=lambda r:r['silhouette']))
  assignments[name]=best_models[name][2].tolist();print('Clustering:',name,report['clustering'][-1],flush=True)
 cluster_best=max(report['clustering'],key=lambda r:r['silhouette']);report['clustering_selected']=cluster_best['algorithm'];report['clustering_features']=features;report['cluster_search_range']=[2,8]
 best_labels=np.array(assignments[cluster_best['algorithm']]);d.assign(cluster=best_labels).to_csv(OUT/'mall_cluster_assignments.csv',index=False);pd.DataFrame(all_cluster).to_csv(OUT/'cluster_all_candidates.csv',index=False)
 joblib.dump({'scaler':scaler,'model':best_models[cluster_best['algorithm']][1],'features':features},OUT/'mall_selected_model.joblib')
 fig,ax=plt.subplots(figsize=(7,4.6));plot=ax.scatter(d[features[0]],d[features[1]],c=best_labels,cmap='tab10',s=34,alpha=.85);ax.set(xlabel=features[0],ylabel=features[1],title=f'Mall customer segments · {cluster_best["algorithm"]}\nk={cluster_best["clusters"]}, silhouette={cluster_best["silhouette"]:.4f}');ax.legend(*plot.legend_elements(),title='Cluster',loc='upper left',fontsize=8);fig.tight_layout();fig.savefig(OUT/'mall_clusters.png');plt.close(fig)
 report['mall_points']=[{'income':int(row[features[0]]),'spending':int(row[features[1]]),'cluster':int(best_labels[i])} for i,(_,row) in enumerate(d.iterrows())]
 for key in ['regression','classification','clustering']:
  pd.DataFrame([{k:v for k,v in r.items() if k not in ['parameters','confusion_matrix']} for r in report[key]]).to_csv(OUT/(key+'_results.csv'),index=False)
 (OUT/'results.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
 print('SELECTED',reg_best['algorithm'],cls_best['algorithm'],cluster_best['algorithm'],flush=True)
 # Verify persisted prediction scores and every selected artifact.
 assert np.isclose(np.sqrt(np.mean((reg_pred['actual']-reg_pred[reg_best['algorithm']])**2)),reg_best['test_rmse'])
 assert np.isclose((cls_pred['actual']==cls_pred[cls_best['algorithm']]).mean(),cls_best['test_accuracy'])
 assert len(best_labels)==200 and len(set(best_labels))==cluster_best['clusters']
 for f in OUT.glob('*.joblib'):joblib.load(f)
 return report
if __name__=='__main__':run()

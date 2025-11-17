from jobstores.sqlalchemy import ClusterCredentialStore

def init_cluster_credentials_store()->ClusterCredentialStore:
    # initializing with a database URL
    _cluster_credentials_store = ClusterCredentialStore(url='sqlite:///clusters.sqlite')
    _cluster_credentials_store.start("clusters")
    return _cluster_credentials_store

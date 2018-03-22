import hashlib, json, traceback, os, datetime
from shutil import copyfile

class jsonenc(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        else:
            return super(jsonenc, self).default(obj)

def get_id(node):
    return hashlib.sha256(node.encode()).hexdigest()

def get_file(ID, filename, input_url, output_dir):
    if input_url[:6] == "files/":
        input_path = input_url[6:]
        path = os.path.dirname(filename)
        files_dir = os.path.join(output_dir,'files',ID)
        try:
            os.mkdir(files_dir)
        except:
            pass
        src = os.path.join(path, input_url)
        dst = os.path.join(files_dir,input_path)
        print("COPY", src, dst)
        copyfile(src, dst)
        return "data/files/"+ID+"/"+input_path

def search_files(base_path, ending):
    return [os.path.join(dirpath,f) for dirpath,dirnames,filenames in os.walk(base_path) for f in filenames if f[-len(ending):] == ending]

def import_metadata(fn):
    print("LOADING: {}".format(fn))
    try:
        with open(fn,"r") as f:
            return json.loads(f.read())
    except:
        traceback.print_exc()
        print("WARNING: no existing metadata found -- assuming empty")
        return {}
    # metadata = {}
    # for node_id in data:
    #     node = data[node_id]
    #     metadata[node['name']] = {'name':node['name']}
    #     metadata[node['name']]['edges'] = {'has':{en:[data[nid]['name'] for nid in node['edges']['has'][en]] for en in node['edges']['has']}}

    # return metadata

def complete_metadata(cat_name, metadata):
    duals = {'has':'is','is':'has'}
    name_to_id = {}
    ans = {}
    cat_id = get_id(cat_name)

    # First, add category
    for node in metadata.values():
        if not 'edges' in node: node['edges'] = {ed:{} for ed in duals}
        node['edges']['has']['category'] = node['edges']['has'].get('category',[])+[cat_name]
    
    # Now, collect all the nodes, explicit and implicit

    # Start with the explicit ones:
    for node in metadata.values():
        node_id = node.get('id',get_id(node['name']))
        name_to_id[node['name']] = node_id
        ans[node_id] = {x:node[x] for x in node}
        ans[node_id]['edges'] = {'has':{},'is':{}}

    # Now go through and find all the implicit ones and give them IDs in name_to_id:
    targets = set()
    for node in metadata.values():
        for et in duals:
            if not et in node['edges']: node['edges'][et] = {}
            edges = node['edges'][et]
            for e in edges:
                targets = targets.union(set(edges[e]))
                
    targets.add(cat_name)
    
    for t in targets:
        if not t in name_to_id:
            node_id = get_id(t)
            print("Implicit node found: {} (ID={})".format(t, node_id))
            name_to_id[t] = node_id
            if t != cat_name: metadata[t] = {'name':t,'edges':{'has':{'category':[cat_name]},'is':{}}}
            ans[node_id] = {'name':t,'edges':{'has':{},'is':{}}}
            
    # Now every node--explicit and implicit--has an ID and an entry in
    # ans (without edges).  Go through and populate edges and dual
    # edges in ans
    for node in metadata.values():
        node_id = name_to_id[node['name']]

        # Add all edges and duals
        for et in duals:
            edges = node['edges'][et]
            for e in edges:
                for target in edges[e]:
                    target_id = name_to_id[target]
                    # Add edge
                    ans[node_id]['edges'][et][e] = ans[node_id]['edges'][et].get(e,[])+[target_id]
                    # Add dualised edge
                    ans[target_id]['edges'][duals[et]][e] = ans[target_id]['edges'][duals[et]].get(e,[])+[node_id]

    return ans

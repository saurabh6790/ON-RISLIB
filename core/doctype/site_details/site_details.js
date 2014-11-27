cur_frm.cscript.validate = function(doc, cdt, cdn){
	child = getchildren('Sub Tenant Details',doc.name,'sub_tenant')
	validate_tenants(doc, cdt ,cdn, child)
	validate_duplication(doc, cdt, cdn, child)
}

validate_tenants = function(doc, cdt, cdn, child){
	if(child.length > doc.no_of_sub_tenant){
		alert("More Tenants Entry than specified limit!!!!")
		throw "More Tenants Entry than specified limit!!!!"
	}
}

validate_duplication = function(doc, cdt, cdn, child){
	var map = {}, i, size;
    for (i = 0; i < child.length; i++){ 	
		if (map[child[i]['sub_tenant_url']]){
			alert("Duplicate URL Fount at possition "+ (i+1))
			throw "Duplicate URL Fount at possition "+ (i+1) 
		}
		map[child[i]['sub_tenant_url']] = true;
		console.log(map)
	}
}
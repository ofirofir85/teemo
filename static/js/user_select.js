function get_members_data(){
	select = document.querySelector('#user_select');
	if (select != null){
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function(){
			if(this.readyState == 4 && this.status == 200){
				response = JSON.parse(this.responseText);
				if (select.isArray == true){
					select.forEach(add_options)
				}
				else{
					add_options(select)
				}
			}
		}
		xhttp.open('GET', api_url, true);
		xhttp.send();
	}
}

function add_options(select){
	response.forEach(add_option);
}

function add_option(member){
	let option = document.createElement('option');
	option.text = member.name;
	option.value = member.id;
	select.add(option);
}
document.addEventListener('DOMContentLoaded', get_members_data);
function tabulation(){
	var textareas = document.getElementsByTagName("textarea");
	for(var i = 0, t = textareas.length; i < t; i++){
		textareas[i].onkeydown = function(e){
			var tab = (e || window.event).keyCode == 9;

			if(tab){ // Si la touche tab est enfoncée
				var scroll = this.scrollTop;
				var tabString = "    ";
				
				if(window.ActiveXObject){
					var textR = document.selection.createRange();
					var selection = textR.text; // On récupère le texte de la sélection
					// On modifie la sélection de manière à ce qu'il y ai la tabulation devant.
					textR.text = tabString + selection;
					// On déplace la sélection du nombre de caractères de la sélection vers la gauche.
					textR.moveStart("character",-selection.length);
					textR.moveEnd("character", 0);
					// On sélectionne le tout
					textR.select();
				}
				else {
					var beforeSelection = this.value.substring(0, this.selectionStart);
					var selection = this.value.substring(this.selectionStart, this.selectionEnd);
					var afterSelection = this.value.substring(this.selectionEnd);
										
					// On modifie le contenu du textarea
					this.value = beforeSelection + tabString + selection + afterSelection;

					// On modifie la sélection
					this.setSelectionRange(beforeSelection.length + tabString.length, beforeSelection.length + tabString.length + selection.length);
				}

				this.focus(); // Met le focus sur le textarea
				this.scrollTop = scroll;
				// Annule l'action de la touche "tabulation". (Empêche de sélectionner le lien suivant)
				return false;
			}
		};
	}
}
tabulation();

var textar="id_description";
var charriot = String.fromCharCode(13);
var LF = String.fromCharCode(10);

function bold(id_text)
{
	style_encadre(id_text, "**", "**");
}

function italic(id_text)
{
	style_encadre(id_text, "*", "*");
}

function h1(id_text)
{
	style_encadre(id_text, "# ", " #");
}

function h2(id_text)
{
	style_encadre(id_text, "## ", " ##");
}

function h3(id_text)
{
	style_encadre(id_text, "### ", " ###");
}

function link(id_text)
{
	var lien = prompt('Saisissez l\'adresse de votre lien', 'http://');
	style_encadre(id_text, "[", "]("+lien+")");
}

function secret(id_text)
{
	style_encadre(id_text, LF+"[secret]{"+charriot, charriot+"}"+LF);
}

function image(id_text)
{
	var url = prompt('Saisissez l\'url de l\'image', 'http://');
	style_encadre(id_text, "![", "]("+url+")");
}

function bulletlist(id_text)
{
	style_precede(id_text, LF, LF, " - ");
}

function numericlist(id_text)
{
	style_precede(id_text, LF, LF, " 1. ",true);
}

function citation(id_text)
{
	var auteur = prompt('Qui est l\'auteur de la citation ?', '');
	
	if(auteur.trim().length==0)
	{
		style_precede(id_text, LF, LF, "> ");
	}
	else
	{
		style_precede(id_text, LF+"**"+auteur+" a écrit : **"+LF, LF, "> ");
	}
}

function code(id_text)
{
	var code = prompt('Quel est le langage (c, c++, java, python, php, html, ...) ?', '');
	var charriot = String.fromCharCode(13);
	style_encadre(id_text, LF+"```"+code+charriot, charriot+"```"+LF);
}

function codeline(id_text)
{
	style_encadre(id_text, "`", "`");
}

function style_encadre(id_text, strdeb, strfin) {
	var textarea = document.getElementById(id_text);
	var scroll = textarea.scrollTop;
	
	if(window.ActiveXObject){
		var textR = document.selection.createRange();
		var selection = textR.text; // On récupère le texte de la sélection
		// On modifie la sélection et on rajoute le texte qu'il faut.
		textR.text = strdeb + selection + strfin;
		// On déplace la sélection du nombre de caractères de la sélection vers la gauche.
		textR.moveStart("character",-selection.length+strfin.length);
		textR.moveEnd("character", strfin.length);
		// On sélectionne le tout
		textR.select();
	}
	else {
		var beforeSelection = textarea.value.substring(0, textarea.selectionStart);
		var selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
		var afterSelection = textarea.value.substring(textarea.selectionEnd);
							
		// On modifie le contenu du textarea
		textarea.value = beforeSelection + strdeb + selection + strfin + afterSelection;

		// On modifie la sélection
		textarea.setSelectionRange(beforeSelection.length + strdeb.length, beforeSelection.length + strdeb.length + selection.length);
	}

	textarea.focus(); // Met le focus sur le textarea
	textarea.scrollTop = scroll;
}

function style_precede(id_text, deb, fin, str, numeric) {
	var textarea = document.getElementById(id_text);
	var scroll = textarea.scrollTop;
	var numeric=numeric||false;

	if(window.ActiveXObject){
		var textR = document.selection.createRange();
		var selection = textR.text; // On récupère le texte de la sélection
		// On modifie la sélection et on rajoute le texte qu'il faut.
		
		var destin=str;
		
		for(var i=0;i<selection.length;i++)
		{
			var cpt=1;
			if(selection.charAt(i)==charriot || selection.charAt(i)==LF) 
				{
					if(numeric) {
						cpt=parseInt(cpt)+1;
						destin=destin+selection.charAt(i)+cpt+". ";
					}
					else
					{
						destin=destin+selection.charAt(i)+str;
					}
				}
			else destin=destin+selection.charAt(i)
		}
		
		textR.text = deb + destin + fin;
		
		// On déplace la sélection du nombre de caractères de la sélection vers la gauche.
		// textR.moveStart("character",-selection.length);
		// textR.moveEnd("character", strfin.length);
		// On sélectionne le tout
		// textR.select();
	}
	else {
		var beforeSelection = textarea.value.substring(0, textarea.selectionStart);
		var selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
		var afterSelection = textarea.value.substring(textarea.selectionEnd);
		
		var destin=str;
		var cpt=1;

		for(var i=0;i<selection.length;i++)
		{
			if(selection.charAt(i)==charriot || selection.charAt(i)==LF) 
				{
					if(numeric) {
						cpt=parseInt(cpt)+1;
						destin=destin+selection.charAt(i)+" "+cpt+". ";
					}
					else
					{
						destin=destin+selection.charAt(i)+str;
					}
				}
			else destin=destin+selection.charAt(i)
		}
		
		// On modifie le contenu du textarea
		textarea.value = beforeSelection + deb + destin + fin + afterSelection;

		// On modifie la sélection
		textarea.setSelectionRange(beforeSelection.length + deb.length, beforeSelection.length + deb.length + destin.length);
	}

	textarea.focus(); // Met le focus sur le textarea
	textarea.scrollTop = scroll;
}

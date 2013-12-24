<%@ page contentType="text/html; charset=utf-8" pageEncoding="UTF-8"%>
<%--
 Licensed to the Apache Software Foundation (ASF) under one or more
 contributor license agreements.  See the NOTICE file distributed with
 this work for additional information regarding copyright ownership.
 The ASF licenses this file to You under the Apache License, Version 2.0
 (the "License"); you may not use this file except in compliance with
 the License.  You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
--%>
<%@ page import="org.apache.lucene.analysis.Analyzer,
                 org.apache.lucene.util.AttributeSource,
                 org.apache.lucene.util.Attribute,
                 org.apache.lucene.analysis.TokenStream,
                 org.apache.lucene.index.Payload,
                 org.apache.lucene.analysis.CharReader,
                 org.apache.lucene.analysis.CharStream,
                 org.apache.lucene.analysis.tokenattributes.*,
                 org.apache.lucene.util.AttributeReflector,
                 org.apache.solr.analysis.CharFilterFactory,
                 org.apache.solr.analysis.TokenFilterFactory,
                 org.apache.solr.analysis.TokenizerChain,
                 org.apache.solr.analysis.TokenizerFactory,
                 org.apache.solr.schema.FieldType,
                 org.apache.solr.schema.SchemaField,
                 org.apache.solr.common.util.XML,
                 javax.servlet.jsp.JspWriter,java.io.IOException
                "%>
<%@ page import="java.io.Reader"%>
<%@ page import="java.io.StringReader"%>
<%@ page import="java.util.*"%>
<%@ page import="java.math.BigInteger" %>

<%-- $Id: analysis.jsp 1095519 2011-04-20 21:30:47Z uschindler $ --%>
<%-- $Source: /cvs/main/searching/org.apache.solrolarServer/resources/admin/analysis.jsp,v $ --%>
<%-- $Name:  $ --%>

<%@include file="header.jsp" %>

<%
  // is name a field name or a type name?
  String nt = request.getParameter("nt");
  if (nt==null || nt.length()==0) nt="name"; // assume field name
  nt = nt.toLowerCase(Locale.ENGLISH).trim();
  String name = request.getParameter("name");
  if (name==null || name.length()==0) name="";
  String val = request.getParameter("val");
  if (val==null || val.length()==0) val="";
  String qval = request.getParameter("qval");
  if (qval==null || qval.length()==0) qval="";
  String verboseS = request.getParameter("verbose");
  boolean verbose = verboseS!=null && verboseS.equalsIgnoreCase("on");
  String qverboseS = request.getParameter("qverbose");
  boolean qverbose = qverboseS!=null && qverboseS.equalsIgnoreCase("on");
  String highlightS = request.getParameter("highlight");
  boolean highlight = highlightS!=null && highlightS.equalsIgnoreCase("on");
%>

<br clear="all">

<h2>Field Analysis</h2>

<form method="POST" action="analysis.jsp" accept-charset="UTF-8">
<table>
<tr>
  <td>
  <strong>Field
          <select name="nt">
    <option <%= nt.equals("name") ? "selected=\"selected\"" : "" %> >name</option>
    <option <%= nt.equals("type") ? "selected=\"selected\"" : "" %>>type</option>
          </select></strong>
  </td>
  <td>
  <input class="std" name="name" type="text" value="<% XML.escapeCharData(name, out); %>">
  </td>
</tr>
<tr>
  <td>
  <strong>Field value (Index)</strong>
  <br/>
  verbose output
  <input name="verbose" type="checkbox"
     <%= verbose ? "checked=\"true\"" : "" %> >
    <br/>
  highlight matches
  <input name="highlight" type="checkbox"
     <%= highlight ? "checked=\"true\"" : "" %> >
  </td>
  <td>
  <textarea class="std" rows="8" cols="70" name="val"><% XML.escapeCharData(val,out); %></textarea>
  </td>
</tr>
<tr>
  <td>
  <strong>Field value (Query)</strong>
  <br/>
  verbose output
  <input name="qverbose" type="checkbox"
     <%= qverbose ? "checked=\"true\"" : "" %> >
  </td>
  <td>
  <textarea class="std" rows="1" cols="70" name="qval"><% XML.escapeCharData(qval,out); %></textarea>
  </td>
</tr>
<tr>

  <td>
  </td>

  <td>
  <input class="stdbutton" type="submit" value="analyze">
  </td>

</tr>
</table>
</form>


<%
  SchemaField field=null;

  if (name!="") {
    if (nt.equals("name")) {
      try {
        field = schema.getField(name);
      } catch (Exception e) {
        out.print("<strong>Unknown Field: ");
        XML.escapeCharData(name, out);
        out.println("</strong>");
      }
    } else {
       FieldType t = schema.getFieldTypes().get(name);
       if (null == t) {
        out.print("<strong>Unknown Field Type: ");
        XML.escapeCharData(name, out);
        out.println("</strong>");
       } else {
         field = new SchemaField("fakefieldoftype:"+name, t);
       }
    }
  }

  if (field!=null) {
    HashSet<String> matches = null;
    if (qval!="" && highlight) {
      Reader reader = new StringReader(qval);
      Analyzer analyzer =  field.getType().getQueryAnalyzer();
      TokenStream tstream = analyzer.reusableTokenStream(field.getName(),reader);
      CharTermAttribute termAtt = tstream.addAttribute(CharTermAttribute.class);
      tstream.reset();
      matches = new HashSet<String>();
      while (tstream.incrementToken()) {
        matches.add(termAtt.toString());
      }
    }

    if (val!="") {
      out.println("<h3>Index Analyzer</h3>");
      doAnalyzer(out, field, val, false, verbose, matches);
    }
    if (qval!="") {
      out.println("<h3>Query Analyzer</h3>");
      doAnalyzer(out, field, qval, true, qverbose, null);
    }
  }

%>


</body>
</html>


<%!
  private static void doAnalyzer(JspWriter out, SchemaField field, String val, boolean queryAnalyser, boolean verbose, Set<String> match) throws Exception {

    FieldType ft = field.getType();
     Analyzer analyzer = queryAnalyser ?
             ft.getQueryAnalyzer() : ft.getAnalyzer();
     if (analyzer instanceof TokenizerChain) {
       TokenizerChain tchain = (TokenizerChain)analyzer;
       CharFilterFactory[] cfiltfacs = tchain.getCharFilterFactories();
       TokenizerFactory tfac = tchain.getTokenizerFactory();
       TokenFilterFactory[] filtfacs = tchain.getTokenFilterFactories();

       if( cfiltfacs != null ){
         String source = val;
         for(CharFilterFactory cfiltfac : cfiltfacs ){
           CharStream reader = CharReader.get(new StringReader(source));
           reader = cfiltfac.create(reader);
           if(verbose){
             writeHeader(out, cfiltfac.getClass(), cfiltfac.getArgs());
             source = writeCharStream(out, reader);
           }
         }
       }

       TokenStream tstream = tfac.create(tchain.charStream(new StringReader(val)));
       List<AttributeSource> tokens = getTokens(tstream);
       if (verbose) {
         writeHeader(out, tfac.getClass(), tfac.getArgs());
       }

       writeTokens(out, tokens, ft, verbose, match);

       for (TokenFilterFactory filtfac : filtfacs) {
         if (verbose) {
           writeHeader(out, filtfac.getClass(), filtfac.getArgs());
         }

         final Iterator<AttributeSource> iter = tokens.iterator();
         tstream = filtfac.create( new TokenStream(tstream.getAttributeFactory()) {
           
           public boolean incrementToken() throws IOException {
             if (iter.hasNext()) {
               clearAttributes();
               AttributeSource token = iter.next();
               Iterator<Class<? extends Attribute>> atts = token.getAttributeClassesIterator();
               while (atts.hasNext()) // make sure all att impls in the token exist here
                 addAttribute(atts.next());
               token.copyTo(this);
               return true;
             } else {
               return false;
             }
           }
          }
         );
         tokens = getTokens(tstream);

         writeTokens(out, tokens, ft, verbose, match);
       }

     } else {
       TokenStream tstream = analyzer.reusableTokenStream(field.getName(),new StringReader(val));
       tstream.reset();
       List<AttributeSource> tokens = getTokens(tstream);
       if (verbose) {
         writeHeader(out, analyzer.getClass(), Collections.EMPTY_MAP);
       }
       writeTokens(out, tokens, ft, verbose, match);
     }
  }


  static List<AttributeSource> getTokens(TokenStream tstream) throws IOException {
    List<AttributeSource> tokens = new ArrayList<AttributeSource>();
    tstream.reset();
    while (tstream.incrementToken()) {
      tokens.add(tstream.cloneAttributes());
    }
    return tokens;
  }

  private static class ReflectItem {
    final Class<? extends Attribute> attClass;
    final String key;
    final Object value;
    
    ReflectItem(Class<? extends Attribute> attClass, String key, Object value) {
      this.attClass = attClass;
      this.key = key;
      this.value = value;
    }
  }
  
  private static class Tok {
    final String term;
    final int pos;
    final List<ReflectItem> reflected = new ArrayList<ReflectItem>();
    
    Tok(AttributeSource token, int pos) {
      this.term = token.addAttribute(CharTermAttribute.class).toString();
      this.pos = pos;
      token.reflectWith(new AttributeReflector() {
        public void reflect(Class<? extends Attribute> attClass, String key, Object value) {
          // leave out position and term
          if (CharTermAttribute.class.isAssignableFrom(attClass))
            return;
          if (PositionIncrementAttribute.class.isAssignableFrom(attClass))
            return;
          reflected.add(new ReflectItem(attClass, key, value));
        }
      });
    }
  }

  private static interface TokToStr {
    public String toStr(Tok o);
  }

  private static void printRow(JspWriter out, String header, String headerTitle, List<Tok>[] arrLst, TokToStr converter, boolean multival, boolean verbose, Set<String> match) throws IOException {
    // find the maximum number of terms for any position
    int maxSz=1;
    if (multival) {
      for (List lst : arrLst) {
        maxSz = Math.max(lst.size(), maxSz);
      }
    }


    for (int idx=0; idx<maxSz; idx++) {
      out.println("<tr>");
      if (idx==0 && verbose) {
        if (header != null) {
          out.print("<th NOWRAP rowspan=\""+maxSz+"\"");
          if (headerTitle != null) {
            out.print(" title=\"");
            XML.escapeCharData(headerTitle,out);
            out.print("\"");
          }
          out.print(">");
          XML.escapeCharData(header,out);
          out.println("</th>");
        }
      }

      for (int posIndex=0; posIndex<arrLst.length; posIndex++) {
        List<Tok> lst = arrLst[posIndex];
        if (lst.size() <= idx) continue;
        if (match!=null && match.contains(lst.get(idx).term)) {
          out.print("<td class=\"highlight\"");
        } else {
          out.print("<td class=\"debugdata\"");
        }

        // if the last value in the column, use up
        // the rest of the space via rowspan.
        if (lst.size() == idx+1 && lst.size() < maxSz) {
          out.print("rowspan=\""+(maxSz-lst.size()+1)+'"');
        }

        out.print('>');

        XML.escapeCharData(converter.toStr(lst.get(idx)), out);
        out.print("</td>");
      }

      out.println("</tr>");
    }

  }

  /* this method is totally broken, as no charset involved: new String(byte[]) is crap!
  static String isPayloadString( Payload p ) {
    String sp = new String(p.getData());
    for( int i=0; i < sp.length(); i++ ) {
      if( !Character.isDefined( sp.charAt(i) ) || Character.isISOControl( sp.charAt(i) ) )
        return "";
      }
    return "(" + sp + ")";
  }
  */

  static void writeHeader(JspWriter out, Class clazz, Map<String,String> args) throws IOException {
    out.print("<h4>");
    out.print(clazz.getName());
    XML.escapeCharData("   "+args,out);
    out.println("</h4>");
  }



  // readable, raw, pos, type, start/end
  static void writeTokens(JspWriter out, List<AttributeSource> tokens, final FieldType ft, boolean verbose, Set<String> match) throws IOException {

    // Use a map to tell what tokens are in what positions
    // because some tokenizers/filters may do funky stuff with
    // very large increments, or negative increments.
    HashMap<Integer,List<Tok>> map = new HashMap<Integer,List<Tok>>();
    boolean needRaw=false;
    int pos=0, reflectionCount = -1;
    for (AttributeSource t : tokens) {
      String text = t.addAttribute(CharTermAttribute.class).toString();
      if (!text.equals(ft.indexedToReadable(text))) {
        needRaw=true;
      }

      pos += t.addAttribute(PositionIncrementAttribute.class).getPositionIncrement();
      List lst = map.get(pos);
      if (lst==null) {
        lst = new ArrayList(1);
        map.put(pos,lst);
      }
      Tok tok = new Tok(t,pos);
      // sanity check
      if (reflectionCount < 0) {
        reflectionCount = tok.reflected.size();
      } else {
        if (reflectionCount != tok.reflected.size())
          throw new RuntimeException("Should not happen: Number of reflected entries differs for position=" + pos);
      }
      lst.add(tok);
    }

    List<Tok>[] arr = (List<Tok>[])map.values().toArray(new ArrayList[map.size()]);

    // Jetty 6.1.3 miscompiles a generics-enabled version..., without generics:
    Arrays.sort(arr, new Comparator() {
      public int compare(Object toks, Object toks1) {
        return ((List<Tok>)toks).get(0).pos - ((List<Tok>)toks1).get(0).pos;
      }
    });

    out.println("<table width=\"auto\" class=\"analysis\" border=\"1\">");

    if (verbose) {
      printRow(out, "position", "calculated from " + PositionIncrementAttribute.class.getName(), arr, new TokToStr() {
        public String toStr(Tok t) {
          return Integer.toString(t.pos);
        }
      },false,verbose,null);
    }

    printRow(out, "term text", CharTermAttribute.class.getName(), arr, new TokToStr() {
      public String toStr(Tok t) {
        return ft.indexedToReadable(t.term);
      }
    },true,verbose,match);

    if (verbose) {
      if (needRaw) {
        printRow(out, "raw text", CharTermAttribute.class.getName(), arr, new TokToStr() {
        public String toStr(Tok t) {
            // page is UTF-8, so anything goes.
            return t.term;
          }
        },true,verbose,match);
      }

      for (int att=0; att < reflectionCount; att++) {
        final ReflectItem item0 = arr[0].get(0).reflected.get(att);
        final int i = att;
        printRow(out, item0.key, item0.attClass.getName(), arr, new TokToStr() {
          public String toStr(Tok t) {
            final ReflectItem item = t.reflected.get(i);
            if (item0.attClass != item.attClass || !item0.key.equals(item.key))
              throw new RuntimeException("Should not happen: attribute types suddenly change at position=" + t.pos);
            if (item.value instanceof Payload) {
              Payload p = (Payload) item.value;
              if( null != p ) {
                BigInteger bi = new BigInteger( p.getData() );
                String ret = bi.toString( 16 );
                if (ret.length() % 2 != 0) {
                  // Pad with 0
                  ret = "0"+ret;
                }
                //TODO maybe fix: ret += isPayloadString(p);
                return ret;
              }
              return "";
            } else {
              return (item.value != null) ? item.value.toString() : "";
            }
          }
        },true,verbose,null);
      }
    }
    
    out.println("</table>");
  }

  static String writeCharStream(JspWriter out, CharStream input) throws IOException {
    out.println("<table width=\"auto\" class=\"analysis\" border=\"1\">");
    out.println("<tr>");

    out.print("<th NOWRAP>");
    XML.escapeCharData("text",out);
    out.println("</th>");

    final int BUFFER_SIZE = 1024;
    char[] buf = new char[BUFFER_SIZE];
    int len = 0;
    StringBuilder sb = new StringBuilder();
    do {
      len = input.read( buf, 0, BUFFER_SIZE );
      if( len > 0 )
        sb.append(buf, 0, len);
    } while( len == BUFFER_SIZE );
    out.print("<td class=\"debugdata\">");
    XML.escapeCharData(sb.toString(),out);
    out.println("</td>");
    
    out.println("</tr>");
    out.println("</table>");
    return sb.toString();
  }

%>

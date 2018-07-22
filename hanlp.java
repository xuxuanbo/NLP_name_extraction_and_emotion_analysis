package org.apache.hadoop.examples;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.*;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.db.DBConfiguration;
import org.apache.hadoop.mapreduce.lib.db.DBInputFormat;
import org.apache.hadoop.mapreduce.lib.db.DBOutputFormat;
import org.apache.hadoop.mapreduce.lib.db.DBWritable;
import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.net.URI;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;
import com.hankcs.hanlp.HanLP;
import com.hankcs.hanlp.seg.Segment;
import com.hankcs.hanlp.seg.CRF.CRFSegment;
import com.hankcs.hanlp.seg.common.Term;
 
public class hanlp {
    private static class MysqlRecord implements DBWritable,Writable {
        protected String movie_id ;
        protected String content ;
        protected String  score ;
 
        @Override
        public void write(PreparedStatement preparedStatement) throws SQLException {
            preparedStatement.setString(1,this.movie_id);
            preparedStatement.setString(2, content);
            preparedStatement.setString(3,this.score);
        }
 
        @Override
        public void readFields(ResultSet resultSet) throws SQLException {
            this.movie_id = resultSet.getString(1) ;
            this.content = resultSet.getString(2);
            this.score = resultSet.getString(3) ;
        }
 
        @Override
        public void write(DataOutput dataOutput) throws IOException {
            dataOutput.writeUTF(movie_id);
            dataOutput.writeUTF(content);
//            Text.writeString(dataOutput, this.time.toString()) ;
            dataOutput.writeUTF(score);
        }
 
        @Override
        public void readFields(DataInput dataInput) throws IOException {
            this.movie_id = dataInput.readUTF() ;
            this.content =dataInput.readUTF();
            this.score = dataInput.readUTF();
        }
 
        @Override
        public String toString() {
            return String.format("%d\t%s\t%d\t%s",movie_id,content,score);
        }
    }

    private static class SQLMapper extends Mapper<Object, MysqlRecord, Text, Text> {
        @Override
        protected void map(Object key, MysqlRecord value, Context context)
                throws IOException, InterruptedException {
            String content = value.content ;
            String movie_id = value.movie_id;
            content = content.replaceAll("\\s|\n", "");
            List<Term> hmm_termList = HanLP.segment(content);
//            System.out.println(hmm_termList);
            for(Term t : hmm_termList)
            {
//            	System.out.print(t.toString().split("/")[1]+"222");
            	if (t.toString().split("/")[1] .equals( "nz" ) )	
            		 context.write(new Text(movie_id),new Text("hmmnz"+t.toString().split("/")[0]));
            	if(t.toString().split("/")[1].equals("nr"))
            		context.write(new Text(movie_id),new Text("hmmnr"+t.toString().split("/")[0]));
            }
            Segment segment = new CRFSegment();
            List<Term> crf_termList = segment.seg(content);
//            System.out.println(crf_termList);
            for(Term t : crf_termList)
            {
//            	System.out.print(t.toString().split("/")[1]+"222");
            	if (t.toString().split("/")[1] .equals( "nz" ) )
            		context.write(new Text(movie_id),new Text("crfnz"+t.toString().split("/")[0]));
            	if(t.toString().split("/")[1].equals("nr" ))
            		context.write(new Text(movie_id),new Text("crfnr"+t.toString().split("/")[0]));
//           
            }
//            System.out.print(content);
//            int uid = value.uid ;
           
        }
    }
 
    private static class SQLReducer extends Reducer<Text, Text,Text,Text> {
        @Override
        protected void reduce(Text key, Iterable<Text> values, Context context)
                throws IOException, InterruptedException {
        	Set<String> actor_name_cr = new HashSet<String>();
        	Set<String> actor_name_cz = new HashSet<String>();
        	Set<String> actor_name_hr = new HashSet<String>();
        	Set<String> actor_name_hz = new HashSet<String>();
        	String s = "";
            for (Text v:values){
            	if(v.toString().startsWith("hmmnr"))
            		actor_name_hr.add(v.toString());
            	if(v.toString().startsWith("hmmnz"))
            		actor_name_hz.add(v.toString());
            	if(v.toString().startsWith("crfnr"))
            		actor_name_cr.add(v.toString());
            	if(v.toString().startsWith("crfnz"))
            		actor_name_cz.add(v.toString());
            }
            for (String str : actor_name_hr) {  
               s+=str+"\001";
          }  
            s+="\002";
            for (String str : actor_name_hz) {  
                s+=str+"\001";
           }  
            s+="\002";
            for (String str : actor_name_cr) {  
                s+=str+"\001";
           }  
            s+="\002";
            for (String str : actor_name_cz) {  
                s+=str+"\001";
           }  
            context.write(key, new Text(s));
        }
    }
 
    public static void main(String[] args) throws Exception{
        Configuration conf = new Configuration() ;
        DBConfiguration.configureDB(
                conf, "com.mysql.jdbc.Driver",
                "jdbc:mysql://192.168.235.55/Seeing_future?&autoReconnect=true&failOverReadOnly=false",
                "root","iiip");
        FileSystem fileSystem = FileSystem.get(new URI("hdfs://localhost:9000/user/hadoopnew/output"), conf);  
        
        //如果输出目录存在就删除  
        if (fileSystem.exists(new Path("hdfs://localhost:9000/user/hadoopnew/output"))){  
            fileSystem.delete(new Path("hdfs://localhost:9000/user/hadoopnew/output"),true);  
        }  
        String[] otherArgs = new GenericOptionsParser(conf, args).getRemainingArgs();
        if (otherArgs.length != 1) {
          System.err.println("Usage: wordcount <in> <out>");
          System.exit(2);
        }
        Job job = Job.getInstance(conf,"mysql test") ;
//        job.addFileToClassPath(new Path("/user/hadoopnew/lib/mysql-connector-java-5.1.44-bin.jar"));

        job.setJarByClass(WordCount.class);
        job.setMapperClass(SQLMapper.class);
        job.setReducerClass(SQLReducer.class);

//        System.out.print("..");
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);
        job.setInputFormatClass(DBInputFormat.class);
        FileOutputFormat.setOutputPath(job, new Path(otherArgs[0])); 
        String[] fields = {"movie_id","content","score"} ; 
        DBInputFormat.setInput(
                job,                // job
                MysqlRecord.class,  // input class
                "douban_comment",      // table name
//                "movie_id = 26861685 or movie_id = 26698897", 
                "",// condition
                "movie_id",             // order by
                fields);            // fields
//        System.out.print(".!!!");
//        DBOutputFormat.setOutput(
//                job,                // job
//                "hadoop_out",       // output table name
//                "date","nums"       // fields
//        );
 
        job.waitForCompletion(true) ;
    }
 
}
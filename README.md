# The Mod Archive Extractor

This program will extract [The Mod Archive](https://modarchive.org/) zip archives. The zip archives can be downloaded
using their [torrent](https://modarchive.org/index.php?faq-torrents) files.

Please note! The program is only intended for operating systems where filenames are case-sensitive. Case-sensitive
names were a conscious choice, as it is perfectly OK for the author that `dope.mod` and `DOPE.MOD` are entirely
different files.

## Structure of Subfolders

Files are unpacked into the subfolder corresponding to their names. The first folders are made from the first letter of
the file names. Second subfolders are created using two first letters from the filenames.

For example song called: `4mat_-_eternity.xm`

```
The_Mod_Archives/
	4/
		4M/
			4mat_-_eternity.xm
```

A third subfolder is created if files with the same name occur. In this case, the subfolder's name will be the original
file name, and file names are prefixed with numbers to distinguish them. However, file saving is only done if the
content differs from previous ones.

For example if we have three modules called `amegas.mod`

```
The_Mod_Archives/
	A/
		AM/
			amegas.mod/
				1-amegas.mod	63048 bytes
				2-amegas.mod	69348 bytes
				3-amegas.mod 	68864 bytes
```

## How to Run

You will need a [Python](https://www.python.org/) interpreter to run the program.
You can then run the program with the command:

```bash
$ python tma_extractor.py   
usage: The Mod Archive Extractor [-h] [-n] input_dir output_dir
The Mod Archive Extractor: error: the following arguments are required: input_dir, output_dir
```

The `input_dir` is the folder where the zip files are stored. The program recursively searches for zip files from
subfolders. The program can also recursively process zips inside zips.

The `output_dir` folder is where you want to extract the files.

## Further Processing

After unpacking, there are a few copies with different names, which can be conveniently replaced with symbolic links
using the [rdfind](https://github.com/pauldreik/rdfind) utility.

```bash
# Replacing duplicates with symbolic links
rdfind -makesymlinks true the_mod_archive
```

The copies were replaced using symbolic links based on absolute paths. Relative paths are often more convenient, 
for example if we want to place files in different folders. This is where another handy program, 
[symlinks](https://github.com/brandt/symlinks), comes in handy.

```bash
# Replacing absolute paths for symbolic links with relative paths
symlinks -cr the_mod_archive
```

Finally, it may be convenient to create a mountable squashfs filesystem of the files.

```bash
# Fine-tuning file rights
chmod -Rv a=rX the_mod_archive
# Making squashfs using zstd compression
mksquashfs the_mod_archive the_mod_archive.sqfs -comp zstd
```

from libc.stdio cimport FILE, fopen, fclose, fwrite

cdef extern from "stdio.h" nogil:
    FILE *fopen(const char *, const char *);
    int fclose(FILE *);
    size_t fwrite(const void *, size_t size, size_t nmemb, FILE *);

cdef void write_no_gil(char* f_name, char* data, int size) nogil:
    cdef FILE* c_file
    c_file = fopen(f_name, "wb")

    fwrite(data, sizeof(data[0]), size, c_file)
    fclose(c_file)

cpdef write_file(file_path, data):
    file_temp = file_path.encode("utf-8")

    cdef int size = len(data)
    cdef char* f_name = file_temp
    cdef char* d = data

    with nogil:
        write_no_gil(f_name, d, size)